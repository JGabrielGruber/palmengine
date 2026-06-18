"""
WizardStepLeaf — interactive leaf bound to a configured wizard step.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState, ContextEngine
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.leaf_support import (
    EventEmitter,
    build_prompt_bundle,
    clear_active_prompt,
    emit_wizard_event,
    enter_wizard_step,
    leave_wizard_step,
    publish_prompt,
)
from palm.patterns.wizard.state import complete_step_input
from palm.patterns.wizard.validation import (
    clear_validation_feedback,
    publish_validation_feedback,
)


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
        return build_prompt_bundle(
            state,
            wizard_name=self._wizard_name,
            step=self._step,
            step_index=self._step_index,
            context=self._context,
            input_key=self.input_key(),
        )

    def _request_input(self, state: BaseState) -> PatternStatus:
        enter_wizard_step(
            state,
            self._step,
            index=self._step_index,
            context=self._context,
        )
        prompt_bundle = self._prompt_bundle(state)
        publish_prompt(state, prompt_key=self.prompt_key(), bundle=prompt_bundle)
        emit_wizard_event(
            self._emit,
            self._wizard_name,
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
            emit_wizard_event(
                self._emit,
                self._wizard_name,
                WizardEventType.VALIDATION_FAILED,
                slug=self._step.slug,
                errors=list(validation.errors),
            )
            return PatternStatus.WAITING_FOR_INPUT

        leave_wizard_step(state, self._step, context=self._context)
        clear_active_prompt(state, prompt_key=self.prompt_key())
        clear_validation_feedback(state)
        emit_wizard_event(
            self._emit,
            self._wizard_name,
            WizardEventType.INPUT_RECEIVED,
            slug=self._step.slug,
            value=value,
            step_index=self._step_index,
        )
        emit_wizard_event(
            self._emit,
            self._wizard_name,
            WizardEventType.STEP_COMPLETED,
            slug=self._step.slug,
            value=value,
            step_index=self._step_index,
        )
        return PatternStatus.SUCCESS
