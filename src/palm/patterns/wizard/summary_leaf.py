"""
WizardSummaryLeaf — review collected answers before commit.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState, ContextEngine
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.state import enter_step, get_answers, leave_step
from palm.patterns.wizard.step_leaf import EventEmitter
from palm.patterns.wizard.validation import (
    clear_validation_feedback,
    publish_validation_feedback,
    validate_collected_answers,
)


class WizardSummaryLeaf(InteractiveLeaf):
    """Presents a summary of answers and requires explicit confirmation."""

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

    def _prompt_bundle(self, state: BaseState, answers: dict[str, Any]) -> dict[str, Any]:
        return {
            "wizard": self._wizard_name,
            "slug": self._step.slug,
            "title": self._step.title,
            "prompt": self._step.prompt,
            "field_type": "confirm",
            "step_kind": "summary",
            "step_index": self._step_index,
            "input_key": self.input_key(),
            "summary": dict(answers),
        }

    def _activate_summary(
        self,
        state: BaseState,
        prompt_bundle: dict[str, Any],
        *,
        answers: dict[str, Any],
        schema_valid: bool,
    ) -> PatternStatus:
        state.set(self.prompt_key(), prompt_bundle)
        state.set(WizardKeys.ACTIVE_PROMPT, prompt_bundle)
        state.set(WizardKeys.CURRENT_STEP, self._step.slug)
        state.set(WizardKeys.STEP_INDEX, self._step_index)
        enter_step(state, self._step.slug, context=self._context)
        self._fire(
            WizardEventType.SUMMARY_SHOWN,
            summary=answers,
            schema_valid=schema_valid,
        )
        self._fire(
            WizardEventType.STEP_STARTED,
            slug=self._step.slug,
            title=self._step.title,
            step_index=self._step_index,
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
            self._fire(
                WizardEventType.VALIDATION_FAILED,
                slug=self._step.slug,
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
            self._fire(
                WizardEventType.VALIDATION_FAILED,
                slug=self._step.slug,
                errors=list(validation.errors),
                reason="summary_schema",
            )
            return PatternStatus.WAITING_FOR_INPUT

        if not _is_affirmative(value):
            publish_validation_feedback(
                state,
                ("Please confirm the summary to continue.",),
                prompt_bundle=self._prompt_bundle(state, answers),
                prompt_key=self.prompt_key(),
            )
            self._fire(WizardEventType.VALIDATION_FAILED, slug=self._step.slug, reason="summary")
            return PatternStatus.WAITING_FOR_INPUT

        state.set(WizardKeys.SUMMARY_ACK, True)
        leave_step(state, self._step.slug, context=self._context)
        state.delete(WizardKeys.ACTIVE_PROMPT)
        clear_validation_feedback(state)
        self._fire(WizardEventType.INPUT_RECEIVED, slug=self._step.slug, value=value)
        return PatternStatus.SUCCESS

    def _fire(self, event_type: str, **payload: Any) -> None:
        if self._emit is not None:
            payload.setdefault("wizard", self._wizard_name)
            self._emit(event_type, payload)


def _is_affirmative(value: Any) -> bool:
    return value in (True, "yes", "Yes", "YES")