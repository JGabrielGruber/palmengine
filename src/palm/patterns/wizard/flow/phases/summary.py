"""
Summary phase — review collected answers before commit.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.context.state import get_answers
from palm.patterns.wizard.bindings.events.support import emit_wizard_event, leave_wizard_step
from palm.patterns.wizard.bindings.events.types import WizardEventType
from palm.patterns.wizard.flow.phases._base import (
    WizardPhaseContext,
    activate_prompt,
    build_phase_prompt,
    clear_phase_prompt,
    is_affirmative,
)
from palm.patterns.wizard.flow.validation import (
    clear_validation_feedback,
    publish_validation_feedback,
    validate_collected_answers,
)


class WizardSummaryLeaf(InteractiveLeaf):
    """Presents a summary of answers and requires explicit confirmation."""

    def __init__(self, ctx: WizardPhaseContext) -> None:
        super().__init__(ctx.step.slug)
        self._ctx = ctx

    def _prompt_bundle(self, state: BaseState, answers: dict[str, Any]) -> dict[str, Any]:
        return build_phase_prompt(
            state,
            self._ctx,
            field_type="confirm",
            step_kind="summary",
            summary=dict(answers),
        )

    def _activate_summary(
        self,
        state: BaseState,
        prompt_bundle: dict[str, Any],
        *,
        answers: dict[str, Any],
        schema_valid: bool,
    ) -> PatternStatus:
        activate_prompt(state, ctx=self._ctx, bundle=prompt_bundle)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.SUMMARY_SHOWN,
            summary=answers,
            schema_valid=schema_valid,
        )
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.STEP_STARTED,
            slug=self._ctx.step.slug,
            title=self._ctx.step.title,
            step_index=self._ctx.step_index,
        )
        return PatternStatus.WAITING_FOR_INPUT

    def _request_input(self, state: BaseState) -> PatternStatus:
        answers = get_answers(state)
        prompt_bundle = self._prompt_bundle(state, answers)
        validation = validate_collected_answers(state, answers)
        if not validation.ok:
            publish_validation_feedback(
                state,
                validation.errors,
                prompt_bundle=prompt_bundle,
                prompt_key=self.prompt_key(),
            )
            emit_wizard_event(
                self._ctx.emit,
                self._ctx.wizard_name,
                WizardEventType.VALIDATION_FAILED,
                slug=self._ctx.step.slug,
                errors=list(validation.errors),
                reason="summary_schema",
            )
            return self._activate_summary(state, prompt_bundle, answers=answers, schema_valid=False)

        clear_validation_feedback(state)
        return self._activate_summary(state, prompt_bundle, answers=answers, schema_valid=True)

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        answers = get_answers(state)
        validation = validate_collected_answers(state, answers)
        if not validation.ok:
            prompt_bundle = self._prompt_bundle(state, answers)
            publish_validation_feedback(
                state,
                validation.errors,
                prompt_bundle=prompt_bundle,
                prompt_key=self.prompt_key(),
            )
            emit_wizard_event(
                self._ctx.emit,
                self._ctx.wizard_name,
                WizardEventType.VALIDATION_FAILED,
                slug=self._ctx.step.slug,
                errors=list(validation.errors),
                reason="summary_schema",
            )
            return PatternStatus.WAITING_FOR_INPUT

        if not is_affirmative(value):
            publish_validation_feedback(
                state,
                ("Please confirm the summary to continue.",),
                prompt_bundle=self._prompt_bundle(state, answers),
                prompt_key=self.prompt_key(),
            )
            emit_wizard_event(
                self._ctx.emit,
                self._ctx.wizard_name,
                WizardEventType.VALIDATION_FAILED,
                slug=self._ctx.step.slug,
                reason="summary",
            )
            return PatternStatus.WAITING_FOR_INPUT

        state.set(WizardKeys.SUMMARY_ACK, True)
        leave_wizard_step(state, self._ctx.step, context=self._ctx.context_engine)
        clear_phase_prompt(state, self._ctx.step.slug)
        clear_validation_feedback(state)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.INPUT_RECEIVED,
            slug=self._ctx.step.slug,
            value=value,
        )
        return PatternStatus.SUCCESS


def build_summary_phase(ctx: WizardPhaseContext) -> WizardSummaryLeaf:
    return WizardSummaryLeaf(ctx)
