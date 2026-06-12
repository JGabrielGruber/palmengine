"""
WizardStepLeaf — interactive leaf bound to a configured wizard step.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.step_scope import (
    begin_step_scope,
    end_step_scope,
    get_answers,
    persist_step_answer,
)
from palm.patterns.wizard.validation import validate_step_input

EventEmitter = Callable[[str, dict[str, Any]], None]


class WizardStepLeaf(InteractiveLeaf):
    """Requests input for one wizard step and persists the answer in state."""

    def __init__(
        self,
        step: WizardStepConfig,
        *,
        wizard_name: str,
        step_index: int,
        emit: EventEmitter | None = None,
    ) -> None:
        super().__init__(step.slug)
        self._step = step
        self._wizard_name = wizard_name
        self._step_index = step_index
        self._emit = emit

    @property
    def step(self) -> WizardStepConfig:
        return self._step

    def _request_input(self, state: BaseState) -> PatternStatus:
        prompt_bundle = {
            "wizard": self._wizard_name,
            "slug": self._step.slug,
            "title": self._step.title,
            "prompt": self._step.prompt,
            "field_type": self._step.field_type,
            "choices": list(self._step.choices),
            "step_index": self._step_index,
            "input_key": self.input_key(),
        }
        state.set(self.prompt_key(), prompt_bundle)
        state.set(WizardKeys.ACTIVE_PROMPT, prompt_bundle)
        state.set(WizardKeys.CURRENT_STEP, self._step.slug)
        state.set(WizardKeys.STEP_INDEX, self._step_index)
        begin_step_scope(state, self._step.slug)
        self._fire(
            WizardEventType.STEP_STARTED,
            slug=self._step.slug,
            title=self._step.title,
            step_index=self._step_index,
        )
        return PatternStatus.WAITING_FOR_INPUT

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        validation = validate_step_input(state, self._step, value)
        if not validation.ok:
            state.set(WizardKeys.VALIDATION_ERROR, validation.errors[0])
            self._fire(
                WizardEventType.VALIDATION_FAILED,
                slug=self._step.slug,
                errors=list(validation.errors),
            )
            return PatternStatus.FAILURE

        persist_step_answer(state, self._step.slug, value)
        end_step_scope(state, self._step.slug)
        state.delete(WizardKeys.ACTIVE_PROMPT)
        state.delete(WizardKeys.VALIDATION_ERROR)
        self._fire(
            WizardEventType.INPUT_RECEIVED,
            slug=self._step.slug,
            value=value,
            step_index=self._step_index,
        )
        return PatternStatus.SUCCESS

    def _fire(self, event_type: str, **payload: Any) -> None:
        if self._emit is not None:
            payload.setdefault("wizard", self._wizard_name)
            self._emit(event_type, payload)


def _get_answers(state: BaseState) -> dict[str, Any]:
    return get_answers(state)
