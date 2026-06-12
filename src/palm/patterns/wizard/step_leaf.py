"""
WizardStepLeaf — interactive leaf bound to a configured wizard step.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState, ContextEngine
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.state import (
    complete_step_input,
    enrich_prompt_bundle,
    enter_step,
    leave_step,
)
from palm.patterns.wizard.validation import (
    clear_validation_feedback,
    publish_validation_feedback,
)

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
        context_engine: ContextEngine | None = None,
    ) -> None:
        super().__init__(step.slug)
        self._step = step
        self._wizard_name = wizard_name
        self._step_index = step_index
        self._emit = emit
        self._context = context_engine

    @property
    def step(self) -> WizardStepConfig:
        return self._step

    def _prompt_bundle(self, state: BaseState) -> dict[str, Any]:
        bundle = {
            "wizard": self._wizard_name,
            "slug": self._step.slug,
            "title": self._step.title,
            "prompt": self._step.prompt,
            "field_type": self._step.field_type,
            "choices": list(self._step.choices),
            "step_index": self._step_index,
            "input_key": self.input_key(),
        }
        return enrich_prompt_bundle(state, bundle, context=self._context)

    def _request_input(self, state: BaseState) -> PatternStatus:
        state.set(WizardKeys.CURRENT_STEP, self._step.slug)
        state.set(WizardKeys.STEP_INDEX, self._step_index)
        enter_step(state, self._step.slug, step=self._step, context=self._context)
        prompt_bundle = self._prompt_bundle(state)
        state.set(self.prompt_key(), prompt_bundle)
        state.set(WizardKeys.ACTIVE_PROMPT, prompt_bundle)
        self._fire(
            WizardEventType.STEP_STARTED,
            slug=self._step.slug,
            title=self._step.title,
            step_index=self._step_index,
        )
        return PatternStatus.WAITING_FOR_INPUT

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        validation = complete_step_input(state, self._step, value)
        if not validation.ok:
            publish_validation_feedback(
                state,
                validation.errors,
                prompt_bundle=self._prompt_bundle(state),
                prompt_key=self.prompt_key(),
            )
            self._fire(
                WizardEventType.VALIDATION_FAILED,
                slug=self._step.slug,
                errors=list(validation.errors),
            )
            return PatternStatus.WAITING_FOR_INPUT

        leave_step(state, self._step.slug, context=self._context)
        state.delete(WizardKeys.ACTIVE_PROMPT)
        clear_validation_feedback(state)
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