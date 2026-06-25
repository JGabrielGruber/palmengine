"""
Commit phase — transactional finalize via registered handlers.
"""

from __future__ import annotations

from typing import Any

from palm.common.resource.compensation import resource_refs_for_compensation
from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.bindings.events.types import WizardEventType
from palm.patterns.wizard.bindings.compensation.handler import CommitContext, CommitResult
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.events.support import emit_wizard_event, leave_wizard_step
from palm.patterns.wizard.flow.phases._base import (
    WizardPhaseContext,
    activate_prompt,
    build_phase_prompt,
    clear_phase_prompt,
    enter_phase_scope,
    is_affirmative,
)
from palm.patterns.wizard.bindings.context.state import get_answers
from palm.patterns.wizard.flow.validation import (
    clear_validation_feedback,
    publish_validation_feedback,
    validate_collected_answers,
)


class WizardCommitLeaf(InteractiveLeaf):
    """Runs a commit handler after the user explicitly confirms."""

    def __init__(self, ctx: WizardPhaseContext, *, hook_name: str) -> None:
        super().__init__(ctx.step.slug)
        self._ctx = ctx
        self._hook_name = hook_name

    def _prompt_bundle(self, state: BaseState) -> dict[str, Any]:
        return build_phase_prompt(
            state,
            self._ctx,
            field_type="confirm",
            step_kind="commit",
            commit_hook=self._hook_name,
        )

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
        answers = get_answers(state)
        validation = validate_collected_answers(state, answers)
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
                reason="commit_schema",
            )
            return PatternStatus.WAITING_FOR_INPUT

        if not is_affirmative(value):
            publish_validation_feedback(
                state,
                ("Please confirm commit to apply your changes.",),
                prompt_bundle=self._prompt_bundle(state),
                prompt_key=self.prompt_key(),
            )
            emit_wizard_event(
                self._ctx.emit,
                self._ctx.wizard_name,
                WizardEventType.VALIDATION_FAILED,
                slug=self._ctx.step.slug,
                reason="commit",
            )
            return PatternStatus.WAITING_FOR_INPUT

        clear_validation_feedback(state)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.COMMIT_STARTED,
            hook=self._hook_name,
        )
        if self._ctx.commit_registry is None:
            return PatternStatus.FAILURE

        context = CommitContext(
            wizard_name=self._ctx.wizard_name,
            state=state,
            answers=get_answers(state),
            hook_name=self._hook_name,
            resource_engine=self._ctx.resource_engine,
        )
        result = self._ctx.commit_registry.run(self._hook_name, context)
        return self._apply_commit_result(result, state)

    def _apply_commit_result(self, result: CommitResult, state: BaseState) -> PatternStatus:
        if result.ok:
            state.set(WizardKeys.COMMITTED, True)
            state.set(WizardKeys.COMMIT_RESULT, result.data)
            if result.data is not None:
                state.set("__result__", result.data)
            state.delete(WizardKeys.COMMIT_ERROR)
            leave_wizard_step(state, self._ctx.step, context=self._ctx.context_engine)
            clear_phase_prompt(state, self._ctx.step.slug)
            emit_wizard_event(
                self._ctx.emit,
                self._ctx.wizard_name,
                WizardEventType.COMMIT_SUCCEEDED,
                hook=self._hook_name,
                data=result.data,
            )
            emit_wizard_event(
                self._ctx.emit,
                self._ctx.wizard_name,
                WizardEventType.INPUT_RECEIVED,
                slug=self._ctx.step.slug,
                value=True,
            )
            return PatternStatus.SUCCESS

        state.set(WizardKeys.COMMIT_ERROR, result.error)
        state.delete(WizardKeys.COMMITTED)
        invocations = state.get(WizardKeys.RESOURCE_INVOCATIONS)
        tracked = list(invocations) if isinstance(invocations, list) else []
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.COMMIT_FAILED,
            hook=self._hook_name,
            error=result.error,
            resource_refs=resource_refs_for_compensation(tracked),
            resource_invocations=tracked,
        )
        return PatternStatus.FAILURE


def build_commit_phase(ctx: WizardPhaseContext, *, hook_name: str | None = None) -> WizardCommitLeaf:
    hook = hook_name or ctx.step.commit_hook
    if not hook:
        raise ValueError(f"Commit step {ctx.step.slug!r} requires commit_hook")
    if ctx.commit_registry is None:
        raise ValueError(f"Commit step {ctx.step.slug!r} requires CommitRegistry")
    return WizardCommitLeaf(ctx, hook_name=hook)