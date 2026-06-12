"""
Wizard state coordination — answers, step scopes, and validated persistence.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.validation import ValidationResult, validate_step_input

if TYPE_CHECKING:
    from palm.patterns.wizard.config import WizardStepConfig
    from palm.patterns.wizard.validation import ValidationRegistry


def get_answers(state: BaseState) -> dict[str, Any]:
    """Return a copy of collected wizard answers."""
    raw = state.get(WizardKeys.ANSWERS)
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def set_answers(state: BaseState, answers: dict[str, Any]) -> None:
    """Replace the wizard answers mapping."""
    state.set(WizardKeys.ANSWERS, dict(answers))


def enter_step(state: BaseState, slug: str) -> None:
    """Enter a step scope when it is not already active."""
    if state.current_scope() != slug:
        state.enter_scope(slug)


def leave_step(state: BaseState, slug: str) -> None:
    """Exit the step scope when it matches ``slug``."""
    if state.current_scope() == slug:
        state.exit_scope()


@contextmanager
def step_scope(state: BaseState, slug: str) -> Generator[BaseState, None, None]:
    """Context manager for synchronous (single-tick) step scopes."""
    enter_step(state, slug)
    try:
        yield state
    finally:
        leave_step(state, slug)


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
    validation = validate_step_input(state, step, value, registry=registry)
    if not validation.ok:
        return validation
    persist_step_answer(state, step.slug, value)
    return validation