"""
WizardResourceLeaf — declarative resource invocation inside a wizard sequence.
"""

from __future__ import annotations

from typing import Any

from palm.common.resource.binding import promote_binding_keys
from palm.common.resource.builder import build_resource_leaf
from palm.common.resource.compensation import is_mutating_action, track_resource_invocation
from palm.core.behavior_tree import LeafNode, PatternStatus
from palm.core.context import BaseState
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.leaf_support import (
    build_prompt_bundle,
    clear_active_prompt,
    emit_wizard_event,
    enter_wizard_step,
    leave_wizard_step,
    publish_prompt,
)
from palm.patterns.wizard.state import get_answers, set_answers
from palm.patterns.wizard.step_leaf import EventEmitter
from palm.patterns.wizard.validation import (
    clear_validation_feedback,
    publish_validation_feedback,
)


def default_resource_prompt(step: WizardStepConfig) -> str:
    """Build the default operator-facing prompt for a resource step."""
    target = step.output_key or step.slug
    return f"Invoking resource {step.resource_ref!r} → {target}"


def format_resource_feedback(
    step: WizardStepConfig,
    *,
    resource_id: str | None = None,
    provider: str | None = None,
    action: str | None = None,
    success: bool = True,
    error: str | None = None,
) -> str:
    """Build CLI feedback after a resource step runs."""
    target = step.output_key or step.slug
    action_label = action or step.resource_action or "invoke"
    provider_label = f" via {provider}" if provider else ""
    status = "OK" if success else "FAILED"
    base = f"[{status}] {step.resource_ref} ({action_label}{provider_label}) → {target}"
    if resource_id:
        base = f"{base} · id={resource_id}"
    if error and not success:
        base = f"{base} · {error}"
    return base


class WizardResourceLeaf(LeafNode):
    """Runs a declarative resource invoke via :class:`~palm.core.behavior_tree.nodes.leaf.resource_leaf.ResourceLeaf`."""

    PROMPT_KEY_PREFIX = "__bt_prompt__"

    def __init__(
        self,
        step: WizardStepConfig,
        *,
        wizard_name: str,
        step_index: int,
        emit: EventEmitter | None = None,
        context_engine: Any | None = None,
        resource_engine: ResourceEngine | None = None,
    ) -> None:
        super().__init__(step.slug)
        if step.step_kind != "resource":
            raise ValueError(
                f"WizardResourceLeaf requires step_kind=resource, got {step.step_kind!r}"
            )
        if not step.resource_ref:
            raise ValueError(f"Resource step {step.slug!r} requires resource_ref")
        self._step = step
        self._wizard_name = wizard_name
        self._step_index = step_index
        self._emit = emit
        self._context = context_engine
        self._inner = build_resource_leaf(
            step.slug,
            resource_engine=resource_engine,
            resource_ref=step.resource_ref,
            action=step.resource_action,
            params=dict(step.params),
            output_key=step.output_key or step.slug,
            error_key=f"{WizardKeys.PREFIX}.resource_error:{step.slug}",
            step_slug=step.slug,
            wizard_name=wizard_name,
        )

    @property
    def step(self) -> WizardStepConfig:
        return self._step

    def prompt_key(self) -> str:
        return f"{self.PROMPT_KEY_PREFIX}:{self._step.slug}"

    def _prompt_bundle(self, state: BaseState) -> dict[str, Any]:
        return build_prompt_bundle(
            state,
            wizard_name=self._wizard_name,
            step=self._step,
            step_index=self._step_index,
            context=self._context,
            include_validation=False,
            prompt=self._step.prompt or default_resource_prompt(self._step),
            field_type="resource",
            resource_ref=self._step.resource_ref,
            output_key=self._step.output_key or self._step.slug,
        )

    def _tick_impl(self, state: BaseState) -> PatternStatus:
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
            step_kind="resource",
            resource_ref=self._step.resource_ref,
        )

        self._promote_answers_for_binding(state)
        status = self._inner.tick(state)

        if status == PatternStatus.SUCCESS:
            result_value = state.get(self._inner.output_key)
            self._persist_resource_result(state, result_value)
            leave_wizard_step(state, self._step, context=self._context)
            clear_active_prompt(state, prompt_key=self.prompt_key())
            clear_validation_feedback(state)
            trace = state.get(self._inner.trace_key)
            trace_dict = trace if isinstance(trace, dict) else {}
            resource_id = trace_dict.get("resource_id")
            action = trace_dict.get("action") or self._step.resource_action
            provider = trace_dict.get("provider")
            if is_mutating_action(str(action) if action else None):
                invocations = state.get(WizardKeys.RESOURCE_INVOCATIONS)
                tracked = list(invocations) if isinstance(invocations, list) else []
                state.set(
                    WizardKeys.RESOURCE_INVOCATIONS,
                    track_resource_invocation(
                        tracked,
                        resource_ref=self._step.resource_ref or "",
                        action=str(action or "invoke"),
                        provider=str(provider) if provider else None,
                        resource_id=str(resource_id) if resource_id else None,
                        step_slug=self._step.slug,
                    ),
                )
            state.set(
                WizardKeys.RESOURCE_FEEDBACK,
                format_resource_feedback(
                    self._step,
                    resource_id=str(resource_id) if resource_id else None,
                    provider=str(provider) if provider else None,
                    action=str(action) if action else None,
                    success=True,
                ),
            )
            state.set(
                f"{WizardKeys.RESOURCE_RESULT}:{self._step.slug}",
                result_value,
            )
            emit_wizard_event(
                self._emit,
                self._wizard_name,
                WizardEventType.STEP_COMPLETED,
                slug=self._step.slug,
                step_index=self._step_index,
                step_kind="resource",
                resource_ref=self._step.resource_ref,
                output_key=self._inner.output_key,
                resource_id=resource_id,
            )
            return PatternStatus.SUCCESS

        message = self._failure_message(state)
        trace = state.get(self._inner.trace_key)
        trace_dict = trace if isinstance(trace, dict) else {}
        state.set(
            WizardKeys.RESOURCE_FEEDBACK,
            format_resource_feedback(
                self._step,
                resource_id=str(trace_dict.get("resource_id"))
                if trace_dict.get("resource_id")
                else None,
                provider=str(trace_dict.get("provider")) if trace_dict.get("provider") else None,
                action=str(trace_dict.get("action") or self._step.resource_action or "invoke"),
                success=False,
                error=message,
            ),
        )
        prompt_bundle = self._prompt_bundle(state)
        prompt_bundle["resource_error"] = message
        publish_validation_feedback(
            state,
            (message,),
            prompt_bundle=prompt_bundle,
            prompt_key=self.prompt_key(),
        )
        emit_wizard_event(
            self._emit,
            self._wizard_name,
            WizardEventType.VALIDATION_FAILED,
            slug=self._step.slug,
            errors=[message],
            step_kind="resource",
            resource_ref=self._step.resource_ref,
        )
        leave_wizard_step(state, self._step, context=self._context)
        return PatternStatus.FAILURE

    def _promote_answers_for_binding(self, state: BaseState) -> None:
        """Expose prior wizard answers on the blackboard for ``{{ state.* }}`` binding."""
        promote_binding_keys(state, get_answers(state))

    def _persist_resource_result(self, state: BaseState, value: Any) -> None:
        if value is None:
            return
        target = self._inner.output_key
        answers = get_answers(state)
        answers[target] = value
        set_answers(state, answers)
        if state.schema is not None:
            state.set_validated(target, value)

    def _failure_message(self, state: BaseState) -> str:
        error_key = f"{WizardKeys.PREFIX}.resource_error:{self._step.slug}"
        raw = state.get(error_key)
        if raw is not None:
            return str(raw)
        trace = state.get(self._inner.trace_key)
        if isinstance(trace, dict) and trace.get("error"):
            return str(trace["error"])
        action = (
            self._step.resource_action or trace.get("action") if isinstance(trace, dict) else None
        )
        action_label = action or "invoke"
        return f"Resource {self._step.resource_ref!r} (action={action_label}) failed"


