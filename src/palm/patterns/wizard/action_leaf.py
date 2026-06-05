"""
WizardActionLeaf — executes a resource provider call during the flow.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import InteractiveLeaf, PatternStatus
from palm.core.context import BaseState
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.step_leaf import EventEmitter
from palm.patterns.wizard.validation import validate_step_value


class WizardActionLeaf(InteractiveLeaf):
    """Confirms then invokes ``ResourceEngine`` for an external action."""

    def __init__(
        self,
        step: WizardStepConfig,
        *,
        wizard_name: str,
        step_index: int,
        resource_engine: ResourceEngine | None,
        emit: EventEmitter | None = None,
    ) -> None:
        super().__init__(step.slug)
        self._step = step
        self._wizard_name = wizard_name
        self._step_index = step_index
        self._resource_engine = resource_engine
        self._emit = emit

    def _request_input(self, state: BaseState) -> PatternStatus:
        prompt_bundle = {
            "wizard": self._wizard_name,
            "slug": self._step.slug,
            "title": self._step.title,
            "prompt": self._step.prompt,
            "field_type": self._step.field_type,
            "step_kind": "action",
            "step_index": self._step_index,
            "input_key": self.input_key(),
            "resource_provider": self._step.resource_provider,
        }
        state.set(self.prompt_key(), prompt_bundle)
        state.set(WizardKeys.ACTIVE_PROMPT, prompt_bundle)
        state.set(WizardKeys.CURRENT_STEP, self._step.slug)
        state.set(WizardKeys.STEP_INDEX, self._step_index)
        self._fire(
            WizardEventType.STEP_STARTED,
            slug=self._step.slug,
            title=self._step.title,
            step_index=self._step_index,
        )
        return PatternStatus.WAITING_FOR_INPUT

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        validation = validate_step_value(self._step, value)
        if not validation.ok:
            state.set(WizardKeys.VALIDATION_ERROR, validation.errors[0])
            self._fire(
                WizardEventType.VALIDATION_FAILED,
                slug=self._step.slug,
                errors=list(validation.errors),
            )
            return PatternStatus.FAILURE

        if self._resource_engine is None or not self._step.resource_provider:
            state.set(WizardKeys.VALIDATION_ERROR, "Resource engine not configured for action")
            return PatternStatus.FAILURE

        resource_id = self._step.resource_id or str(value)
        provider = self._resource_engine.use(self._step.resource_provider)
        result = provider.fetch(resource_id)
        state.set(f"{WizardKeys.RESOURCE_RESULT}:{self._step.slug}", result)
        state.delete(WizardKeys.ACTIVE_PROMPT)
        state.delete(WizardKeys.VALIDATION_ERROR)
        self._fire(
            WizardEventType.ACTION_EXECUTED,
            slug=self._step.slug,
            provider=self._step.resource_provider,
            resource_id=resource_id,
        )
        return PatternStatus.SUCCESS

    def _fire(self, event_type: str, **payload: Any) -> None:
        if self._emit is not None:
            payload.setdefault("wizard", self._wizard_name)
            self._emit(event_type, payload)