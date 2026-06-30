"""
Input phase — interactive wizard steps that collect operator answers.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.bindings.context.state import complete_step_input
from palm.patterns.wizard.bindings.events.support import emit_wizard_event, leave_wizard_step
from palm.patterns.wizard.bindings.events.types import WizardEventType
from palm.patterns.wizard.flow.phases._base import (
    WizardPhaseContext,
    activate_prompt,
    build_phase_prompt,
    clear_phase_prompt,
    enter_phase_scope,
)
from palm.patterns.wizard.flow.validation import (
    clear_validation_feedback,
    publish_validation_feedback,
)


class WizardInputLeaf(InteractiveLeaf):
    """Requests input for one wizard step and persists the answer in state."""

    def __init__(self, ctx: WizardPhaseContext) -> None:
        super().__init__(ctx.step.slug)
        self._ctx = ctx

    @property
    def step(self):
        return self._ctx.step

    def _prompt_bundle(self, state: BaseState) -> dict[str, Any]:
        return build_phase_prompt(state, self._ctx)

    def _request_input(self, state: BaseState) -> PatternStatus:
        enter_phase_scope(state, self._ctx)
        activate_prompt(
            state,
            ctx=self._ctx,
            bundle=self._prompt_bundle(state),
            event_type=WizardEventType.STEP_STARTED,
        )
        return PatternStatus.WAITING_FOR_INPUT

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        validation = complete_step_input(state, self._ctx.step, value)
        if not validation.ok:
            publish_validation_feedback(
                state,
                validation.errors,
                prompt_bundle=self._prompt_bundle(state),
                prompt_key=self.prompt_key(),
            )
            emit_wizard_event(
                self._ctx.emit,
                self._ctx.wizard_name,
                WizardEventType.VALIDATION_FAILED,
                slug=self._ctx.step.slug,
                errors=list(validation.errors),
            )
            return PatternStatus.WAITING_FOR_INPUT

        leave_wizard_step(state, self._ctx.step, context=self._ctx.context_engine)
        clear_phase_prompt(state, self._ctx.step.slug)
        clear_validation_feedback(state)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.INPUT_RECEIVED,
            slug=self._ctx.step.slug,
            value=value,
            step_index=self._ctx.step_index,
        )
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.STEP_COMPLETED,
            slug=self._ctx.step.slug,
            value=value,
            step_index=self._ctx.step_index,
        )
        return PatternStatus.SUCCESS


def build_input_phase(ctx: WizardPhaseContext) -> WizardInputLeaf:
    return WizardInputLeaf(ctx)
