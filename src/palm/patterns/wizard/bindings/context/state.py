"""
Wizard state coordination — answers, step scopes, and validated persistence.

Each input step enters a named scope (the step slug). :func:`enter_step` binds
per-step schemas; :func:`complete_step_input` validates, coerces, and persists
answers. :func:`leave_step` exits the scope on success so the sequence advances.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.flow.validation import (
    ValidationResult,
    prepare_step_input,
    validate_prepared_step_input,
)

if TYPE_CHECKING:
    from palm.core.context import ContextEngine
    from palm.core.context.state_schema import StateSchema
    from palm.patterns.wizard.bindings.definitions.config import WizardStepConfig
    from palm.patterns.wizard.flow.validation import ValidationRegistry


def scope_prompt_fields(
    state: BaseState,
    *,
    context: ContextEngine | None = None,
) -> dict[str, Any]:
    """Return scope metadata for wizard prompt bundles."""
    if context is not None:
        stack = context.state_scope_stack
        depth = context.state_scope_depth
        current = context.current_state_scope
    else:
        stack = state.scope_stack()
        depth = state.scope_depth()
        current = state.current_scope()
    fields: dict[str, Any] = {
        "scope_stack": list(stack),
        "scope_depth": depth,
    }
    if current is not None:
        fields["current_scope"] = current
    return fields


def enrich_prompt_bundle(
    state: BaseState,
    bundle: dict[str, Any],
    *,
    context: ContextEngine | None = None,
    include_validation: bool = True,
) -> dict[str, Any]:
    """Add scope and validation context to a wizard prompt bundle."""
    enriched = dict(bundle)
    enriched.update(scope_prompt_fields(state, context=context))
    if include_validation:
        errors = state.get(WizardKeys.VALIDATION_ERRORS)
        if isinstance(errors, list) and errors:
            enriched["validation_errors"] = errors
            error = state.get(WizardKeys.VALIDATION_ERROR)
            if error is not None:
                enriched["validation_error"] = error
    return enriched


def get_answers(state: BaseState) -> dict[str, Any]:
    """Return a copy of collected wizard answers."""
    raw = state.get(WizardKeys.ANSWERS)
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def set_answers(state: BaseState, answers: dict[str, Any]) -> None:
    """Replace the wizard answers mapping."""
    state.set(WizardKeys.ANSWERS, dict(answers))


def merge_compositional_state_into_answers(state: BaseState) -> bool:
    """
    Promote pre-submitted blackboard keys into wizard answers when absent.

    Compositional child flows receive ``initial_state`` on the job blackboard;
    commit handlers and transforms read :data:`~WizardKeys.ANSWERS`, so keys
    such as ``capture_role`` must be mirrored there before steps run.
    """
    snapshot_fn = getattr(state, "snapshot", None)
    if not callable(snapshot_fn):
        return False

    answers = get_answers(state)
    changed = False
    for key, value in snapshot_fn().items():
        if not _is_compositional_state_key(key):
            continue
        if key in answers and answers[key] is not None:
            continue
        if value is None:
            continue
        answers[key] = value
        changed = True

    if changed:
        set_answers(state, answers)
    return changed


def _is_compositional_state_key(key: str) -> bool:
    if key.startswith(WizardKeys.PREFIX):
        return False
    if key.startswith("__"):
        return False
    return True


def enter_step(
    state: BaseState,
    slug: str,
    *,
    step: WizardStepConfig | None = None,
    context: ContextEngine | None = None,
    scope_schema: StateSchema | None = None,
) -> None:
    """Enter a step scope and optionally bind a per-scope schema."""
    schema = scope_schema
    if schema is None and step is not None and step.schema is not None:
        schema = step.schema
    if schema is not None:
        state.bind_scope_schema(slug, schema)

    if context is not None:
        if context.current_state is not state:
            context.bind_state(state)
        if context.current_state_scope != slug:
            context.enter_state_scope(slug)
        return

    if state.current_scope() != slug:
        state.enter_scope(slug)


def leave_step(
    state: BaseState,
    slug: str,
    *,
    context: ContextEngine | None = None,
) -> None:
    """Exit the step scope when it matches ``slug``."""
    if context is not None:
        if context.current_state_scope == slug:
            context.exit_state_scope()
        return
    if state.current_scope() == slug:
        state.exit_scope()


@contextmanager
def step_scope(
    state: BaseState,
    slug: str,
    *,
    step: WizardStepConfig | None = None,
    context: ContextEngine | None = None,
) -> Generator[BaseState, None, None]:
    """Context manager for synchronous (single-tick) step scopes."""
    enter_step(state, slug, step=step, context=context)
    try:
        yield state
    finally:
        leave_step(state, slug, context=context)


def persist_step_answer(state: BaseState, slug: str, value: Any) -> None:
    """Store an answer and promote schema-backed values to validated root keys."""
    answers = get_answers(state)
    answers[slug] = value
    set_answers(state, answers)
    if state.schema is None:
        return
    state.set_scoped("answer", value)
    state.set_validated(slug, value)


def complete_step_input(
    state: BaseState,
    step: WizardStepConfig,
    value: Any,
    *,
    registry: ValidationRegistry | None = None,
) -> ValidationResult:
    """Validate ``value`` and persist it when all checks pass."""
    value, choice_error = prepare_step_input(state, step, value)
    if choice_error is not None:
        return choice_error
    validation = validate_prepared_step_input(state, step, value, registry=registry)
    if not validation.ok:
        return validation
    persist_step_answer(state, step.slug, value)
    return validation
