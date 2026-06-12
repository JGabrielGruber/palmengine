"""
WizardCommitLeaf — explicit transactional commit via registered handlers.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.handler import CommitContext, CommitRegistry, CommitResult
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.state import enter_step, get_answers, leave_step
from palm.patterns.wizard.step_leaf import EventEmitter


class WizardCommitLeaf(InteractiveLeaf):
    """Runs a commit handler after the user explicitly confirms."""

    def __init__(
        self,
        step: WizardStepConfig,
        *,
        wizard_name: str,
        step_index: int,
        hook_name: str,
        commit_registry: CommitRegistry,
        resource_engine: ResourceEngine | None = None,
        emit: EventEmitter | None = None,
    ) -> None:
        super().__init__(step.slug)
        self._step = step
        self._wizard_name = wizard_name
        self._step_index = step_index
        self._hook_name = hook_name
        self._commit_registry = commit_registry
        self._resource_engine = resource_engine
        self._emit = emit

    def _request_input(self, state: BaseState) -> PatternStatus:
        prompt_bundle = {
            "wizard": self._wizard_name,
            "slug": self._step.slug,
            "title": self._step.title,
            "prompt": self._step.prompt,
            "field_type": "confirm",
            "step_kind": "commit",
            "step_index": self._step_index,
            "input_key": self.input_key(),
            "commit_hook": self._hook_name,
        }
        state.set(self.prompt_key(), prompt_bundle)
        state.set(WizardKeys.ACTIVE_PROMPT, prompt_bundle)
        state.set(WizardKeys.CURRENT_STEP, self._step.slug)
        state.set(WizardKeys.STEP_INDEX, self._step_index)
        enter_step(state, self._step.slug)
        self._fire(
            WizardEventType.STEP_STARTED,
            slug=self._step.slug,
            title=self._step.title,
            step_index=self._step_index,
        )
        return PatternStatus.WAITING_FOR_INPUT

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        if not _is_affirmative(value):
            state.set(WizardKeys.VALIDATION_ERROR, "Commit must be explicitly confirmed")
            self._fire(WizardEventType.VALIDATION_FAILED, slug=self._step.slug, reason="commit")
            return PatternStatus.FAILURE

        self._fire(WizardEventType.COMMIT_STARTED, hook=self._hook_name)
        context = CommitContext(
            wizard_name=self._wizard_name,
            state=state,
            answers=get_answers(state),
            hook_name=self._hook_name,
            resource_engine=self._resource_engine,
        )
        result = self._commit_registry.run(self._hook_name, context)
        return self._apply_commit_result(result, state)

    def _apply_commit_result(self, result: CommitResult, state: BaseState) -> PatternStatus:
        if result.ok:
            state.set(WizardKeys.COMMITTED, True)
            state.set(WizardKeys.COMMIT_RESULT, result.data)
            state.delete(WizardKeys.COMMIT_ERROR)
            leave_step(state, self._step.slug)
            state.delete(WizardKeys.ACTIVE_PROMPT)
            self._fire(
                WizardEventType.COMMIT_SUCCEEDED,
                hook=self._hook_name,
                data=result.data,
            )
            self._fire(WizardEventType.INPUT_RECEIVED, slug=self._step.slug, value=True)
            return PatternStatus.SUCCESS

        state.set(WizardKeys.COMMIT_ERROR, result.error)
        state.delete(WizardKeys.COMMITTED)
        self._fire(
            WizardEventType.COMMIT_FAILED,
            hook=self._hook_name,
            error=result.error,
        )
        return PatternStatus.FAILURE

    def _fire(self, event_type: str, **payload: Any) -> None:
        if self._emit is not None:
            payload.setdefault("wizard", self._wizard_name)
            self._emit(event_type, payload)


def _is_affirmative(value: Any) -> bool:
    return value in (True, "yes", "Yes", "YES")
