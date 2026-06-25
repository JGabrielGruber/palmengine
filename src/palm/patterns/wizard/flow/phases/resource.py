"""
Resource phase — declarative ResourceLeaf invocation inside a wizard step.
"""

from __future__ import annotations

from typing import Any

from palm.common.resource.binding import promote_binding_keys
from palm.common.resource.builder import build_resource_leaf
from palm.common.resource.compensation import is_mutating_action, track_resource_invocation
from palm.core.behavior_tree import LeafNode, PatternStatus
from palm.core.context import BaseState
from palm.core.orchestration import JobStatus
from palm.patterns._registry import get_child_wait_hooks
from palm.patterns.wizard.bindings.resource.child_wait import (
    child_job_id_from_wait,
    child_wait_from_result,
    clear_child_wait,
    default_child_wait_prompt,
    get_child_wait,
    set_child_wait,
)
from palm.patterns.wizard.bindings.definitions.config import WizardStepConfig
from palm.patterns.wizard.bindings.events.types import WizardEventType
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.events.support import (
    build_prompt_bundle,
    clear_active_prompt,
    emit_wizard_event,
    enter_wizard_step,
    leave_wizard_step,
    publish_prompt,
)
from palm.patterns.wizard.flow.phases._base import WizardPhaseContext, wizard_prompt_key
from palm.patterns.wizard.bindings.context.state import get_answers, set_answers
from palm.patterns.wizard.flow.validation import (
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

    def __init__(self, ctx: WizardPhaseContext) -> None:
        step = ctx.step
        super().__init__(step.slug)
        if step.step_kind != "resource":
            raise ValueError(
                f"WizardResourceLeaf requires step_kind=resource, got {step.step_kind!r}"
            )
        if not step.resource_ref:
            raise ValueError(f"Resource step {step.slug!r} requires resource_ref")
        self._ctx = ctx
        self._inner = build_resource_leaf(
            step.slug,
            resource_engine=ctx.resource_engine,
            resource_ref=step.resource_ref,
            action=step.resource_action,
            params=dict(step.params),
            output_key=step.output_key or step.slug,
            error_key=f"{WizardKeys.PREFIX}.resource_error:{step.slug}",
            step_slug=step.slug,
            wizard_name=ctx.wizard_name,
        )

    def prompt_key(self) -> str:
        return wizard_prompt_key(self._ctx.step.slug)

    def _prompt_bundle(self, state: BaseState, *, prompt: str | None = None) -> dict[str, Any]:
        step = self._ctx.step
        bundle = build_prompt_bundle(
            state,
            wizard_name=self._ctx.wizard_name,
            step=step,
            step_index=self._ctx.step_index,
            context=self._ctx.context_engine,
            include_validation=False,
            prompt=prompt or step.prompt or default_resource_prompt(step),
            field_type="resource",
            auto_advance=True,
            resource_ref=step.resource_ref,
            output_key=step.output_key or step.slug,
        )
        waiting = get_child_wait(state)
        if waiting:
            bundle["waiting_for_child"] = True
            bundle["waiting_for_child_job_id"] = waiting.get("child_job_id")
            bundle["waiting_for_child_instance_id"] = waiting.get("child_instance_id")
            bundle["child_job_href"] = waiting.get("child_job_href")
            bundle["child_instance_href"] = waiting.get("child_instance_href")
            bundle["child_status"] = waiting.get("child_status")
        return bundle

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        pending = get_child_wait(state)
        if pending and pending.get("step_slug") == self._ctx.step.slug:
            return self._poll_child_wait(state, pending)

        enter_wizard_step(
            state,
            self._ctx.step,
            index=self._ctx.step_index,
            context=self._ctx.context_engine,
        )

        prompt_bundle = self._prompt_bundle(state)
        publish_prompt(state, prompt_key=self.prompt_key(), bundle=prompt_bundle)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.STEP_STARTED,
            slug=self._ctx.step.slug,
            title=self._ctx.step.title,
            step_index=self._ctx.step_index,
            step_kind="resource",
            resource_ref=self._ctx.step.resource_ref,
        )

        self._promote_answers_for_binding(state)
        status = self._inner.tick(state)

        if status == PatternStatus.WAITING_FOR_CHILD:
            return self._enter_child_wait(state)

        if status == PatternStatus.SUCCESS:
            return self._complete_success(state)

        return self._fail_step(state)

    def _enter_child_wait(self, state: BaseState) -> PatternStatus:
        result_value = state.get(self._inner.output_key)
        waiting = child_wait_from_result(
            result_value if isinstance(result_value, dict) else {},
            step_slug=self._ctx.step.slug,
            output_key=self._inner.output_key,
            resource_ref=self._ctx.step.resource_ref,
        )
        set_child_wait(state, waiting)

        prompt = default_child_wait_prompt(waiting)
        publish_prompt(
            state,
            prompt_key=self.prompt_key(),
            bundle=self._prompt_bundle(state, prompt=prompt),
        )
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.CHILD_WAITING,
            slug=self._ctx.step.slug,
            step_index=self._ctx.step_index,
            child_job_id=waiting.get("child_job_id"),
            child_instance_id=waiting.get("child_instance_id"),
            child_status=waiting.get("child_status"),
        )
        state.set(
            WizardKeys.RESOURCE_FEEDBACK,
            format_resource_feedback(
                self._ctx.step,
                success=True,
                action="submit_flow",
                provider="palm",
            )
            + " · waiting for nested wizard",
        )
        return PatternStatus.WAITING_FOR_CHILD

    def _poll_child_wait(self, state: BaseState, waiting: dict[str, Any]) -> PatternStatus:
        child_job_id = child_job_id_from_wait(waiting)
        if not child_job_id:
            return self._fail_step(state, message="Missing child_job_id while waiting for child")

        child_wait = get_child_wait_hooks("wizard")
        child_job = (
            child_wait.poll_child_for_parent(state, child_job_id) if child_wait is not None else None
        )
        if child_job is None:
            publish_prompt(
                state,
                prompt_key=self.prompt_key(),
                bundle=self._prompt_bundle(
                    state,
                    prompt=default_child_wait_prompt(waiting),
                ),
            )
            return PatternStatus.WAITING_FOR_CHILD
        if child_job is None:
            return self._fail_step(state, message=f"Child job not found: {child_job_id!r}")

        waiting["child_status"] = child_job.status.value
        set_child_wait(state, waiting)

        if child_job.status == JobStatus.SUCCEEDED:
            payload = dict(waiting.get("child_payload") or {})
            payload.update(
                {
                    "job_id": child_job.id,
                    "instance_id": child_job.metadata.get("instance_id"),
                    "status": child_job.status.value,
                    "result": child_job.result,
                    "waiting_for_child_wizard": False,
                }
            )
            state.set(self._inner.output_key, payload)
            clear_child_wait(state)
            emit_wizard_event(
                self._ctx.emit,
                self._ctx.wizard_name,
                WizardEventType.CHILD_COMPLETED,
                slug=self._ctx.step.slug,
                step_index=self._ctx.step_index,
                child_job_id=child_job.id,
                child_status=child_job.status.value,
            )
            return self._complete_success(state)

        if child_job.status in {JobStatus.FAILED, JobStatus.CANCELLED}:
            clear_child_wait(state)
            return self._fail_step(
                state,
                message=f"Nested wizard {child_job_id!r} ended with {child_job.status.value}",
            )

        publish_prompt(
            state,
            prompt_key=self.prompt_key(),
            bundle=self._prompt_bundle(state, prompt=default_child_wait_prompt(waiting)),
        )
        return PatternStatus.WAITING_FOR_CHILD

    def _complete_success(self, state: BaseState) -> PatternStatus:
        result_value = state.get(self._inner.output_key)
        self._persist_resource_result(state, result_value)
        leave_wizard_step(state, self._ctx.step, context=self._ctx.context_engine)
        clear_active_prompt(state, prompt_key=self.prompt_key())
        clear_validation_feedback(state)
        trace = state.get(self._inner.trace_key)
        trace_dict = trace if isinstance(trace, dict) else {}
        resource_id = trace_dict.get("resource_id")
        action = trace_dict.get("action") or self._ctx.step.resource_action
        provider = trace_dict.get("provider")
        if is_mutating_action(str(action) if action else None):
            invocations = state.get(WizardKeys.RESOURCE_INVOCATIONS)
            tracked = list(invocations) if isinstance(invocations, list) else []
            state.set(
                WizardKeys.RESOURCE_INVOCATIONS,
                track_resource_invocation(
                    tracked,
                    resource_ref=self._ctx.step.resource_ref or "",
                    action=str(action or "invoke"),
                    provider=str(provider) if provider else None,
                    resource_id=str(resource_id) if resource_id else None,
                    step_slug=self._ctx.step.slug,
                ),
            )
        state.set(
            WizardKeys.RESOURCE_FEEDBACK,
            format_resource_feedback(
                self._ctx.step,
                resource_id=str(resource_id) if resource_id else None,
                provider=str(provider) if provider else None,
                action=str(action) if action else None,
                success=True,
            ),
        )
        state.set(
            f"{WizardKeys.RESOURCE_RESULT}:{self._ctx.step.slug}",
            result_value,
        )
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.STEP_COMPLETED,
            slug=self._ctx.step.slug,
            step_index=self._ctx.step_index,
            step_kind="resource",
            resource_ref=self._ctx.step.resource_ref,
            output_key=self._inner.output_key,
            resource_id=resource_id,
        )
        return PatternStatus.SUCCESS

    def _fail_step(self, state: BaseState, *, message: str | None = None) -> PatternStatus:
        detail = message or self._failure_message(state)
        trace = state.get(self._inner.trace_key)
        trace_dict = trace if isinstance(trace, dict) else {}
        state.set(
            WizardKeys.RESOURCE_FEEDBACK,
            format_resource_feedback(
                self._ctx.step,
                resource_id=str(trace_dict.get("resource_id"))
                if trace_dict.get("resource_id")
                else None,
                provider=str(trace_dict.get("provider")) if trace_dict.get("provider") else None,
                action=str(trace_dict.get("action") or self._ctx.step.resource_action or "invoke"),
                success=False,
                error=detail,
            ),
        )
        prompt_bundle = self._prompt_bundle(state)
        prompt_bundle["resource_error"] = detail
        publish_validation_feedback(
            state,
            (detail,),
            prompt_bundle=prompt_bundle,
            prompt_key=self.prompt_key(),
        )
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.VALIDATION_FAILED,
            slug=self._ctx.step.slug,
            errors=[detail],
            step_kind="resource",
            resource_ref=self._ctx.step.resource_ref,
        )
        leave_wizard_step(state, self._ctx.step, context=self._ctx.context_engine)
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
        error_key = f"{WizardKeys.PREFIX}.resource_error:{self._ctx.step.slug}"
        raw = state.get(error_key)
        if raw is not None:
            return str(raw)
        trace = state.get(self._inner.trace_key)
        if isinstance(trace, dict) and trace.get("error"):
            return str(trace["error"])
        action = (
            self._ctx.step.resource_action or trace.get("action") if isinstance(trace, dict) else None
        )
        action_label = action or "invoke"
        return f"Resource {self._ctx.step.resource_ref!r} (action={action_label}) failed"


def build_resource_phase(ctx: WizardPhaseContext) -> WizardResourceLeaf:
    return WizardResourceLeaf(ctx)