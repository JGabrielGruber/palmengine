"""
Wizard transform integration — resource fetch, pipeline apply, choice extraction.
"""

from __future__ import annotations

from typing import Any

from palm.common.transforms.pipeline import apply_pipeline, resolve_transform_engine
from palm.common.transforms.spec import TransformPipeline
from palm.core.context import BaseState
from palm.core.resource import ResourceEngine
from palm.core.transform.engine import TransformEngine
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.keys import WizardKeys


def fetch_step_resource(
    step: WizardStepConfig,
    *,
    resource_engine: ResourceEngine | None,
    state: BaseState,
) -> Any:
    """Load raw step data from a configured resource provider."""
    if resource_engine is None or not step.resource_provider:
        raise RuntimeError(f"Step {step.slug!r} requires a resource provider")
    resource_id = step.resource_id
    if not resource_id:
        answers = state.get(WizardKeys.ANSWERS)
        if isinstance(answers, dict) and step.slug in answers:
            resource_id = str(answers[step.slug])
        else:
            raise RuntimeError(f"Step {step.slug!r} requires resource_id or prior answer")
    provider = resource_engine.use(step.resource_provider)
    return provider.fetch(resource_id)


def apply_step_transform(
    step: WizardStepConfig,
    value: Any,
    *,
    transform_engine: TransformEngine | None = None,
) -> Any:
    """Apply the step transform pipeline when configured."""
    if step.transform is None:
        return value
    context = apply_pipeline(step.transform, value, engine=transform_engine)
    return context.value


def load_transformed_step_data(
    step: WizardStepConfig,
    *,
    resource_engine: ResourceEngine | None,
    transform_engine: TransformEngine | None,
    state: BaseState,
) -> Any:
    """Fetch (optional) resource data and apply transforms for a wizard step."""
    engine = resolve_transform_engine(transform_engine)
    raw: Any
    if step.resource_provider:
        raw = fetch_step_resource(step, resource_engine=resource_engine, state=state)
    else:
        raw = state.get(f"{WizardKeys.RESOURCE_RESULT}:{step.slug}")
        if raw is None:
            raise RuntimeError(f"Step {step.slug!r} has no resource data to transform")
    transformed = apply_step_transform(step, raw, transform_engine=engine)
    state.set(f"{WizardKeys.TRANSFORM_RESULT}:{step.slug}", transformed)
    return transformed


def choices_from_value(
    data: Any,
    *,
    label_key: str = "label",
    value_key: str | None = None,
) -> tuple[str, ...]:
    """
    Build wizard choice labels from transformed data.

    When ``value_key`` is set, choices use ``"{label} ({value})"`` for disambiguation.
    """
    if isinstance(data, list):
        choices: list[str] = []
        for item in data:
            if isinstance(item, dict):
                label = item.get(label_key)
                if label is None:
                    continue
                text = str(label)
                if value_key and value_key in item:
                    text = f"{text} ({item[value_key]})"
                choices.append(text)
            elif item is not None:
                choices.append(str(item))
        return tuple(choices)
    if isinstance(data, dict) and label_key in data:
        return (str(data[label_key]),)
    if isinstance(data, str):
        return (data,)
    return ()


def resolve_step_choices(
    step: WizardStepConfig,
    *,
    resource_engine: ResourceEngine | None,
    transform_engine: TransformEngine | None,
    state: BaseState,
) -> tuple[str, ...]:
    """Resolve dynamic choices for a choice step (resource + transform)."""
    if step.choices:
        return step.choices
    if step.transform is None:
        return ()
    data = load_transformed_step_data(
        step,
        resource_engine=resource_engine,
        transform_engine=transform_engine,
        state=state,
    )
    return choices_from_value(
        data,
        label_key=step.choices_label_key,
        value_key=step.choices_value_key,
    )