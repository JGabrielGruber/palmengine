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
from palm.executions.exceptions import DefinitionBuildError
from palm.patterns.wizard import WizardConfig, WizardPattern, WizardStepConfig

_WIZARD_FIELD_TYPES = frozenset({"text", "choice", "confirm"})


def build_pattern(
    flow: FlowDefinition,
    *,
    event_engine: EventEngine | None = None,
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

    if flow.pattern == "wizard":
        return _build_wizard(
            pattern_cls,
            name=flow.name,
            options=flow.options,
            event_engine=event_engine,
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
    config = options.get("config")
    if isinstance(config, WizardConfig):
        return config

    allow_backtrack = bool(options.get("allow_backtrack", True))

    steps_value = options.get("steps")
    if isinstance(steps_value, WizardConfig):
        return steps_value
    if isinstance(steps_value, int):
        slugs = [f"step_{i + 1}" for i in range(steps_value)]
        return WizardConfig.from_slugs(slugs, allow_backtrack=allow_backtrack)

    if isinstance(steps_value, list) and steps_value:
        if isinstance(steps_value[0], str):
            return WizardConfig.from_slugs(
                list(steps_value),
                allow_backtrack=allow_backtrack,
            )
        if isinstance(steps_value[0], dict):
            built = tuple(_step_from_mapping(item) for item in steps_value)
            intro = options.get("introduction_slug")
            return WizardConfig(
                steps=built,
                allow_backtrack=allow_backtrack,
                introduction_slug=str(intro) if intro is not None else None,
            )

    step_count = options.get("step_count")
    if isinstance(step_count, int):
        slugs = [f"step_{i + 1}" for i in range(step_count)]
        return WizardConfig.from_slugs(slugs, allow_backtrack=allow_backtrack)

    raise DefinitionBuildError(
        "Wizard flow requires 'config', 'steps' (slugs or step dicts), or 'step_count'"
    )


def _build_wizard(
    pattern_cls: type[BasePattern],
    *,
    name: str,
    options: dict[str, Any],
    event_engine: EventEngine | None,
) -> BasePattern:
    if not issubclass(pattern_cls, WizardPattern):
        raise DefinitionBuildError("Registry entry for 'wizard' is not WizardPattern")

    if not options:
        return pattern_cls(name=name, event_engine=event_engine)

    raw_config = options.get("config")
    if isinstance(raw_config, WizardConfig):
        return pattern_cls(name=name, config=raw_config, event_engine=event_engine)

    config = wizard_config_from_options(options)
    return pattern_cls(name=name, config=config, event_engine=event_engine)


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

    return WizardStepConfig(
        slug=str(slug),
        title=str(title),
        prompt=str(prompt),
        field_type=field_type,
        choices=choices,
        required=bool(data.get("required", True)),
    )