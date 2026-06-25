"""
Wizard pattern builder — parse flow options into ``WizardPattern`` instances.
"""

from __future__ import annotations

from typing import Any

from palm.common.exceptions import DefinitionBuildError
from palm.common.patterns.build_context import PatternBuildContext
from palm.core.behavior_tree import BasePattern
from palm.definitions.flow import FlowDefinition
from palm.patterns.wizard.bindings.definitions.config import WizardConfig, WizardStepConfig
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.definitions.options import parse_wizard_flow_options
from palm.patterns.wizard.pattern import WizardPattern
from palm.patterns.wizard.flow.phases.resource import default_resource_prompt
from palm.patterns.wizard.flow.phases.transform import default_transform_prompt
from palm.patterns.wizard.bindings.definitions.kinds import WizardStepKind
from palm.patterns.wizard.flow.extensions.registry import default_wizard_step_registry
from palm.patterns.wizard.flow.validation import StepValidationRule

_WIZARD_FIELD_TYPES = frozenset({"text", "choice", "confirm"})


def build(
    flow: FlowDefinition,
    context: PatternBuildContext,
    pattern_cls: type[BasePattern],
) -> BasePattern:
    """Instantiate a wizard pattern from a flow definition."""
    if not issubclass(pattern_cls, WizardPattern):
        raise DefinitionBuildError("Registry entry for 'wizard' is not WizardPattern")

    commit_registry = context.commit_registry
    if commit_registry is None:
        from palm.patterns.wizard.bindings.compensation.handler import default_commit_registry

        commit_registry = default_commit_registry()

    kwargs: dict[str, Any] = {
        "name": flow.name,
        "event_engine": context.event_engine,
        "resource_engine": context.resource_engine,
        "commit_registry": commit_registry,
    }

    options = flow.options
    if not options:
        return pattern_cls(**kwargs)

    raw_config = options.get("config")
    if isinstance(raw_config, WizardConfig):
        config = materialize_wizard_step_schemas(
            raw_config,
            context.definition_repository,
        )
        return pattern_cls(config=config, **kwargs)

    config = wizard_config_from_options(options)
    config = materialize_wizard_step_schemas(config, context.definition_repository)
    if config.include_commit and not config.commit_hook:
        hook = options.get("commit_hook")
        if not hook:
            raise DefinitionBuildError(
                "Wizard with include_commit requires 'commit_hook' in flow options"
            )
    return pattern_cls(config=config, **kwargs)


def wizard_config_from_options(options: dict[str, Any]) -> WizardConfig:
    """Build ``WizardConfig`` from flow ``options`` (wizard flows only)."""
    options = parse_wizard_flow_options(options)
    config = options.get("config")
    if isinstance(config, WizardConfig):
        return config

    allow_backtrack = bool(options.get("allow_backtrack", True))
    include_summary = bool(options.get("include_summary", False))
    include_commit = bool(options.get("include_commit", False))
    commit_hook = options.get("commit_hook")
    introduction_slug = options.get("introduction_slug")

    steps_value = options.get("steps")
    if isinstance(steps_value, WizardConfig):
        return steps_value
    if isinstance(steps_value, int):
        slugs = [f"step_{i + 1}" for i in range(steps_value)]
        return WizardConfig.from_slugs(
            slugs,
            allow_backtrack=allow_backtrack,
            include_summary=include_summary,
            include_commit=include_commit,
            commit_hook=str(commit_hook) if commit_hook else None,
        )

    if isinstance(steps_value, list) and steps_value:
        if isinstance(steps_value[0], str):
            return WizardConfig.from_slugs(
                list(steps_value),
                allow_backtrack=allow_backtrack,
                include_summary=include_summary,
                include_commit=include_commit,
                commit_hook=str(commit_hook) if commit_hook else None,
            )
        if isinstance(steps_value[0], dict):
            built = tuple(_step_from_mapping(item) for item in steps_value)
            return WizardConfig(
                steps=built,
                allow_backtrack=allow_backtrack,
                introduction_slug=str(introduction_slug) if introduction_slug else None,
                include_summary=include_summary,
                include_commit=include_commit,
                commit_hook=str(commit_hook) if commit_hook else None,
            )

    step_count = options.get("step_count")
    if isinstance(step_count, int):
        slugs = [f"step_{i + 1}" for i in range(step_count)]
        return WizardConfig.from_slugs(
            slugs,
            allow_backtrack=allow_backtrack,
            include_summary=include_summary,
            include_commit=include_commit,
            commit_hook=str(commit_hook) if commit_hook else None,
        )

    raise DefinitionBuildError(
        "Wizard flow requires 'config', 'steps' (slugs or step dicts), or 'step_count'"
    )


def _step_from_mapping(data: dict[str, Any]) -> WizardStepConfig:
    slug = data.get("slug")
    if not slug:
        raise DefinitionBuildError("Wizard step dict requires 'slug'")

    field_type = data.get("field_type", "text")
    if field_type not in _WIZARD_FIELD_TYPES:
        raise DefinitionBuildError(f"Invalid wizard field_type: {field_type!r}")

    choices = data.get("choices", ())
    if isinstance(choices, list):
        choices = tuple(choices)

    title = data.get("title", str(slug).replace("_", " ").title())
    prompt = data.get("prompt", f"Enter value for {slug}")

    validation_raw = data.get("validation", ())
    validation: tuple[StepValidationRule, ...] = ()
    if isinstance(validation_raw, list):
        validation = tuple(
            StepValidationRule(
                rule=str(item["rule"]),
                params=dict(item.get("params") or {}),
            )
            for item in validation_raw
            if isinstance(item, dict) and "rule" in item
        )

    step_kind: WizardStepKind = data.get("step_kind", "input")
    if step_kind == "action":
        raise DefinitionBuildError(
            "step_kind 'action' was removed in 0.12; use step_kind 'resource' with resource_ref",
        )
    if not default_wizard_step_registry().has(step_kind):
        available = default_wizard_step_registry().names()
        raise DefinitionBuildError(
            f"Invalid wizard step_kind: {step_kind!r}. "
            f"Register custom kinds via default_wizard_step_registry().register(...). "
            f"Available: {available}"
        )

    inline_schema = data.get("state_schema")
    state_schema = dict(inline_schema) if isinstance(inline_schema, dict) else None
    ref = data.get("state_schema_ref")
    state_schema_ref = str(ref) if ref else None

    from palm.patterns.wizard.flow.collection.config import CollectionFieldConfig

    item_fields: tuple[CollectionFieldConfig, ...] = ()
    collection_key = data.get("collection_key")
    min_items = int(data.get("min_items", 1))
    label_field = data.get("label_field")
    if step_kind == "collection":
        from palm.patterns.wizard.flow.collection.config import item_fields_from_mapping

        item_fields = item_fields_from_mapping(data.get("item_fields"), repository=None)

    raw_params = data.get("params")
    step_params = dict(raw_params) if isinstance(raw_params, dict) else {}

    if step_kind == "resource" and prompt == f"Enter value for {slug}":
        if not data.get("resource_ref"):
            raise DefinitionBuildError(
                f"Resource step {slug!r} requires 'resource_ref'",
            )
        preview = WizardStepConfig(
            slug=str(slug),
            title=str(title),
            prompt=str(prompt),
            step_kind="resource",
            resource_ref=str(data["resource_ref"]),
            output_key=data.get("output_key"),
        )
        prompt = default_resource_prompt(preview)

    transform = None
    if step_kind == "transform":
        from palm.common.transforms.builder import transform_step_from_mapping

        transform_data = dict(data)
        transform_data.setdefault("name", slug)
        transform_data.setdefault("error_key", f"{WizardKeys.PREFIX}.transform_error:{slug}")
        transform = transform_step_from_mapping(transform_data)
        if prompt == f"Enter value for {slug}":
            prompt = default_transform_prompt(
                WizardStepConfig(
                    slug=str(slug),
                    title=str(title),
                    prompt=str(prompt),
                    step_kind="transform",
                    transform=transform,
                ),
            )

    return WizardStepConfig(
        slug=str(slug),
        title=str(title),
        prompt=str(prompt),
        field_type=field_type,
        choices=choices,
        required=bool(data.get("required", True)),
        step_kind=step_kind,
        validation=validation,
        state_schema=state_schema,
        state_schema_ref=state_schema_ref,
        commit_hook=data.get("commit_hook"),
        resource_ref=str(data["resource_ref"]) if data.get("resource_ref") else None,
        resource_action=str(data["action"]) if data.get("action") else None,
        params=step_params,
        output_key=str(data["output_key"]) if data.get("output_key") else None,
        allow_backtrack=data.get("allow_backtrack"),
        collection_key=str(collection_key) if collection_key else None,
        item_fields=item_fields,
        min_items=min_items,
        label_field=str(label_field) if label_field else None,
        transform=transform,
    )


def materialize_wizard_step_schemas(
    config: WizardConfig,
    repository: Any | None = None,
) -> WizardConfig:
    """Resolve declarative step schemas and attach materialized instances."""
    steps = tuple(_materialize_step(step, repository) for step in config.steps)
    if steps == config.steps:
        return config
    return WizardConfig(
        steps=steps,
        allow_backtrack=config.allow_backtrack,
        introduction_slug=config.introduction_slug,
        include_summary=config.include_summary,
        include_commit=config.include_commit,
        summary_slug=config.summary_slug,
        commit_slug=config.commit_slug,
        commit_hook=config.commit_hook,
    )


def _materialize_step(
    step: WizardStepConfig,
    repository: Any | None,
) -> WizardStepConfig:
    item_fields = step.item_fields
    if step.step_kind == "collection" and item_fields:
        from palm.patterns.wizard.flow.collection.config import item_fields_from_mapping

        raw_fields = [
            {
                "slug": field.slug,
                "title": field.title,
                "prompt": field.prompt,
                "field_type": field.field_type,
                "choices": list(field.choices),
                "required": field.required,
                "validation": [
                    {"rule": rule.rule, "params": dict(rule.params)} for rule in field.validation
                ],
                "state_schema": field.state_schema,
                "state_schema_ref": field.state_schema_ref,
            }
            for field in item_fields
        ]
        item_fields = item_fields_from_mapping(raw_fields, repository=repository)

    schema = step.schema
    if schema is None and step.has_state_schema:
        schema = step.materialize_state_schema(repository)

    if schema is step.schema and item_fields == step.item_fields:
        return step

    return WizardStepConfig(
        slug=step.slug,
        title=step.title,
        prompt=step.prompt,
        field_type=step.field_type,
        choices=step.choices,
        required=step.required,
        step_kind=step.step_kind,
        validation=step.validation,
        state_schema=step.state_schema,
        state_schema_ref=step.state_schema_ref,
        schema=schema,
        commit_hook=step.commit_hook,
        resource_ref=step.resource_ref,
        resource_action=step.resource_action,
        params=dict(step.params),
        output_key=step.output_key,
        allow_backtrack=step.allow_backtrack,
        collection_key=step.collection_key,
        item_fields=item_fields,
        min_items=step.min_items,
        label_field=step.label_field,
        transform=step.transform,
    )
