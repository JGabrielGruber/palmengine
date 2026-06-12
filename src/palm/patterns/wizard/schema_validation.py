"""
Wizard schema validation — step-level and commit-time checks against state schemas.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState, StateSchema
from palm.core.exceptions import StateValidationError

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.patterns.wizard.config import WizardConfig, WizardStepConfig


def validate_schema_value(
    schema: StateSchema,
    value: Any,
    *,
    path: str,
) -> list[str]:
    """Validate ``value`` against a materialized schema document."""
    return schema.validate_value(value, path=path)


def validate_step_schema_errors(step: WizardStepConfig, value: Any) -> list[str]:
    """Return step-schema validation errors for ``value``."""
    schema = step.schema
    if schema is None:
        return []
    return validate_schema_value(schema, value, path=step.slug)


def validate_flow_schema_key_errors(
    state: BaseState,
    step_slug: str,
    value: Any,
) -> list[str]:
    """Return flow-schema validation errors for a single answer key."""
    schema = state.schema
    if schema is None:
        return []
    try:
        schema.validate_key(step_slug, value)
    except StateValidationError as exc:
        return [str(exc)]
    return []


def validate_collected_answers_errors(
    state: BaseState,
    answers: Mapping[str, Any],
) -> list[str]:
    """Return flow-schema validation errors for the full answers mapping."""
    schema = state.schema
    if schema is None:
        return []
    return schema.validate_state(dict(answers))


def materialize_wizard_step_schemas(
    config: WizardConfig,
    repository: DefinitionRepository | None = None,
) -> WizardConfig:
    """Resolve declarative step schemas and attach materialized instances."""
    from palm.patterns.wizard.config import WizardConfig

    steps = tuple(_materialize_step_schema(step, repository) for step in config.steps)
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


def _materialize_step_schema(
    step: WizardStepConfig,
    repository: DefinitionRepository | None,
) -> WizardStepConfig:
    from palm.patterns.wizard.config import WizardStepConfig

    if step.schema is not None or not step.has_state_schema:
        return step
    schema = step.materialize_state_schema(repository)
    if schema is None:
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
        resource_provider=step.resource_provider,
        resource_id=step.resource_id,
        allow_backtrack=step.allow_backtrack,
    )