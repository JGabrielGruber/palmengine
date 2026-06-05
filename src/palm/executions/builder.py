"""
Definition builder — resolves ``FlowDefinition`` into concrete patterns.
"""

from __future__ import annotations

from typing import Any

import palm.patterns  # noqa: F401 — register patterns
from palm.core.behavior_tree import BasePattern
from palm.core.event import EventEngine
from palm.core.registry import pattern_registry
from palm.definitions.flow import FlowDefinition
from palm.executions.build_context import PatternBuildContext
from palm.executions.exceptions import DefinitionBuildError
from palm.executions.wizard_options import parse_wizard_flow_options
from palm.patterns.wizard import WizardConfig, WizardPattern, WizardStepConfig
from palm.patterns.wizard.step_kinds import WizardStepKind
from palm.patterns.wizard.validation import StepValidationRule

_WIZARD_FIELD_TYPES = frozenset({"text", "choice", "confirm"})
_WIZARD_STEP_KINDS = frozenset({"input", "introduction", "summary", "commit", "action"})


def build_pattern(
    flow: FlowDefinition,
    *,
    event_engine: EventEngine | None = None,
    context: PatternBuildContext | None = None,
) -> BasePattern:
    """
    Instantiate a registered pattern from a flow definition.

    Pattern-specific option parsing lives here so core orchestration stays
    unaware of definitions.
    """
    try:
        pattern_cls = pattern_registry.get(flow.pattern)
    except Exception as exc:
        raise DefinitionBuildError(
            f"Cannot resolve pattern {flow.pattern!r} for flow {flow.name!r}"
        ) from exc

    ctx = context or PatternBuildContext(event_engine=event_engine)
    if event_engine is not None and ctx.event_engine is None:
        ctx.event_engine = event_engine

    if flow.pattern == "wizard":
        return _build_wizard(
            pattern_cls,
            name=flow.name,
            options=flow.options,
            context=ctx,
        )

    if flow.pattern in ("dag", "etl"):
        allowed = {"name"}
        unknown = set(flow.options) - allowed
        if unknown:
            raise DefinitionBuildError(
                f"Pattern {flow.pattern!r} does not support options: {sorted(unknown)}"
            )
        return pattern_cls(name=flow.options.get("name", flow.name))

    if flow.options:
        raise DefinitionBuildError(
            f"Pattern {flow.pattern!r} does not support flow options yet"
        )

    return pattern_cls(name=flow.name)


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


def _build_wizard(
    pattern_cls: type[BasePattern],
    *,
    name: str,
    options: dict[str, Any],
    context: PatternBuildContext,
) -> BasePattern:
    if not issubclass(pattern_cls, WizardPattern):
        raise DefinitionBuildError("Registry entry for 'wizard' is not WizardPattern")

    kwargs: dict[str, Any] = {
        "name": name,
        "event_engine": context.event_engine,
        "resource_engine": context.resource_engine,
        "commit_registry": context.resolved_commit_registry,
    }

    if not options:
        return pattern_cls(**kwargs)

    raw_config = options.get("config")
    if isinstance(raw_config, WizardConfig):
        return pattern_cls(config=raw_config, **kwargs)

    config = wizard_config_from_options(options)
    if config.include_commit and not config.commit_hook:
        hook = options.get("commit_hook")
        if not hook:
            raise DefinitionBuildError(
                "Wizard with include_commit requires 'commit_hook' in flow options"
            )
    return pattern_cls(config=config, **kwargs)


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
    if step_kind not in _WIZARD_STEP_KINDS:
        raise DefinitionBuildError(f"Invalid wizard step_kind: {step_kind!r}")

    return WizardStepConfig(
        slug=str(slug),
        title=str(title),
        prompt=str(prompt),
        field_type=field_type,
        choices=choices,
        required=bool(data.get("required", True)),
        step_kind=step_kind,
        validation=validation,
        commit_hook=data.get("commit_hook"),
        resource_provider=data.get("resource_provider"),
        resource_id=data.get("resource_id"),
        allow_backtrack=data.get("allow_backtrack"),
    )