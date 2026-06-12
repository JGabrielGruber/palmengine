"""
Wizard step scoping — coordinate ``BaseState`` scopes during interactive steps.
"""

from __future__ import annotations

from typing import Any

from palm.core.context import BaseState
from palm.patterns.wizard.keys import WizardKeys


def get_answers(state: BaseState) -> dict[str, Any]:
    raw = state.get(WizardKeys.ANSWERS)
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def begin_step_scope(state: BaseState, slug: str) -> None:
    """Enter a step-named scope when it is not already active."""
    if state.current_scope() != slug:
        state.enter_scope(slug)


def end_step_scope(state: BaseState, slug: str) -> None:
    """Exit the active scope when it matches ``slug``."""
    if state.current_scope() == slug:
        state.exit_scope()


def persist_step_answer(state: BaseState, slug: str, value: Any) -> None:
    """Store an answer in wizard state and promote schema-backed values."""
    answers = get_answers(state)
    answers[slug] = value
    state.set(WizardKeys.ANSWERS, answers)
    if state.schema is None:
        return
    state.set_scoped("answer", value)
    state.set_validated(slug, value)