"""
Resource phase — declarative ResourceLeaf invocation inside a wizard step.
"""

from __future__ import annotations

from typing import Any

from palm.common.operator.resource_remediation import resource_invoke_remediation
from palm.common.resource.binding import promote_binding_keys
from palm.common.resource.builder import build_resource_leaf
from palm.common.resource.compensation import is_mutating_action, track_resource_invocation
from palm.system.subsystems.planes.wait.present import waiting_on_row
from palm.core.behavior_tree import LeafNode, PatternStatus
from palm.core.context import BaseState
from palm.core.orchestration import JobStatus
from palm.core.wait import WaitInterest
from plugins.patterns.wizard.bindings.context.keys import WizardKeys
from plugins.patterns.wizard.bindings.context.state import get_answers, set_answers
from plugins.patterns.wizard.bindings.definitions.config import WizardStepConfig
from plugins.patterns.wizard.bindings.events.support import (
    build_prompt_bundle,
    clear_active_prompt,
    emit_wizard_event,
    enter_wizard_step,
    leave_wizard_step,
    publish_prompt,
)
from plugins.patterns.wizard.bindings.events.types import WizardEventType
from plugins.patterns.wizard.bindings.resource.nested_park import (
    clear_nested_park,
    default_nested_prompt,
    nested_park_for_step,
    open_nested_park,
    park_meta_from_result,
)
from plugins.patterns.wizard.flow.phases._base import WizardPhaseContext, wizard_prompt_key
from plugins.patterns.wizard.flow.validation import (
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
        interest = nested_park_for_step(state, self._ctx.step.slug)
        if interest is not None:
            # Durable park is interest; prompt carries the same row as inspect.
            row = waiting_on_row(interest)
            meta = interest.meta or {}
            if meta.get("child_job_href"):
                row["child_job_href"] = meta["child_job_href"]
            if meta.get("child_instance_href"):
                row["child_instance_href"] = meta["child_instance_href"]
            bundle["waiting_on"] = [row]
        return bundle

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        pending = nested_park_for_step(state, self._ctx.step.slug)
        if pending is not None:
            # Interest still open → wait for continue plane.
            return self._hold_nested_park(state, pending)

        # Plane delivered nested success (interest closed; output written).
        if self._nested_output_delivered(state):
            return self._finish_nested_delivered(state)

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

        if status == PatternStatus.WAITING_FOR_INPUT:
            raw = state.get(self._inner.output_key)
            if isinstance(raw, dict) and raw.get("nested_park"):
                return self._enter_nested_park(state)
            # Unexpected yield from resource leaf — stay parked with prompt.
            return PatternStatus.WAITING_FOR_INPUT

        if status == PatternStatus.SUCCESS:
            return self._complete_success(state)

        return self._handle_resource_failure(state)

    def _nested_output_delivered(self, state: BaseState) -> bool:
        """True when WaitPlaneService wrote child success onto output_key."""
        raw = state.get(self._inner.output_key)
        if not isinstance(raw, dict):
            return False
        if raw.get("nested_park"):
            return False
        status = str(raw.get("status") or "").upper()
        return status == JobStatus.SUCCEEDED.value

    def _finish_nested_delivered(self, state: BaseState) -> PatternStatus:
        raw = state.get(self._inner.output_key)
        child_id = None
        child_status = JobStatus.SUCCEEDED.value
        if isinstance(raw, dict):
            child_id = raw.get("job_id")
            child_status = str(raw.get("status") or child_status)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.CHILD_COMPLETED,
            slug=self._ctx.step.slug,
            step_index=self._ctx.step_index,
            child_job_id=child_id,
            child_status=child_status,
        )
        return self._complete_success(state)

    def _enter_nested_park(self, state: BaseState) -> PatternStatus:
        result_value = state.get(self._inner.output_key)
        park = park_meta_from_result(
            result_value if isinstance(result_value, dict) else {},
            step_slug=self._ctx.step.slug,
            output_key=self._inner.output_key,
            resource_ref=self._ctx.step.resource_ref,
        )
        interest = open_nested_park(
            state, target_id=park["target_id"], meta=park["meta"]
        )

        prompt = default_nested_prompt(interest)
        publish_prompt(
            state,
            prompt_key=self.prompt_key(),
            bundle=self._prompt_bundle(state, prompt=prompt),
        )
        meta = interest.meta or {}
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.CHILD_WAITING,
            slug=self._ctx.step.slug,
            step_index=self._ctx.step_index,
            child_job_id=interest.target_id,
            child_instance_id=meta.get("child_instance_id"),
            child_status=meta.get("child_status"),
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
        return PatternStatus.WAITING_FOR_INPUT

    def _hold_nested_park(self, state: BaseState, interest: WaitInterest) -> PatternStatus:
        """Interest still open: wait for continue plane (no poll completion path)."""
        child_job_id = interest.target_id

        # Plane already delivered + interest lag.
        if self._nested_output_delivered(state):
            clear_nested_park(state, target_id=child_job_id)
            return self._finish_nested_delivered(state)

        publish_prompt(
            state,
            prompt_key=self.prompt_key(),
            bundle=self._prompt_bundle(state, prompt=default_nested_prompt(interest)),
        )
        return PatternStatus.WAITING_FOR_INPUT

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
        feedback = format_resource_feedback(
            self._ctx.step,
            resource_id=str(resource_id) if resource_id else None,
            provider=str(provider) if provider else None,
            action=str(action) if action else None,
            success=True,
        )
        # Surface hermetic / spawn stdout so Assist turns show the return value.
        if isinstance(result_value, dict):
            stdout = result_value.get("stdout_tail")
            if isinstance(stdout, str) and stdout.strip():
                preview = stdout.strip()
                if len(preview) > 500:
                    preview = preview[-500:]
                feedback = f"{feedback}\n--- stdout ---\n{preview}"
        state.set(WizardKeys.RESOURCE_FEEDBACK, feedback)
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

    def _failure_mode(self) -> str:
        params = self._ctx.step.params or {}
        mode = str(params.get("on_resource_failure") or "block").lower()
        if mode not in {"block", "skip", "branch"}:
            return "block"
        return mode

    def _failure_context(self, state: BaseState, *, message: str | None = None) -> tuple[str, dict[str, Any], str | None]:
        detail = message or self._failure_message(state)
        trace = state.get(self._inner.trace_key)
        trace_dict = trace if isinstance(trace, dict) else {}
        remediation = resource_invoke_remediation(
            error=detail,
            resource_ref=self._ctx.step.resource_ref,
            provider=str(trace_dict.get("provider")) if trace_dict.get("provider") else None,
        )
        return detail, trace_dict, remediation

    def _handle_resource_failure(self, state: BaseState) -> PatternStatus:
        mode = self._failure_mode()
        detail, trace_dict, remediation = self._failure_context(state)

        if mode == "skip":
            return self._complete_recovered(
                state,
                detail=detail,
                remediation=remediation,
                recovery="skip",
            )

        if mode == "branch":
            branch_target = (self._ctx.step.params or {}).get("on_resource_failure_branch")
            if not branch_target:
                return self._fail_step(
                    state,
                    message=(
                        f"{detail} (on_resource_failure=branch requires "
                        "on_resource_failure_branch step param)"
                    ),
                    remediation=remediation,
                )
            state.set(WizardKeys.JUMP_TO_STEP, str(branch_target))
            return self._complete_recovered(
                state,
                detail=detail,
                remediation=remediation,
                recovery="branch",
                branch_target=str(branch_target),
            )

        return self._fail_step(state, message=detail, remediation=remediation, trace_dict=trace_dict)

    def _complete_recovered(
        self,
        state: BaseState,
        *,
        detail: str,
        remediation: str | None,
        recovery: str,
        branch_target: str | None = None,
    ) -> PatternStatus:
        output_key = self._inner.output_key
        state.set(output_key, None)
        leave_wizard_step(state, self._ctx.step, context=self._ctx.context_engine)
        clear_active_prompt(state, prompt_key=self.prompt_key())
        clear_validation_feedback(state)

        recovery_note = f"resource failure recovered via {recovery}"
        if branch_target:
            recovery_note = f"{recovery_note} → {branch_target}"
        feedback = format_resource_feedback(
            self._ctx.step,
            success=False,
            error=f"{detail} · {recovery_note}",
        )
        state.set(WizardKeys.RESOURCE_FEEDBACK, feedback)
        state.set(f"{WizardKeys.RESOURCE_RESULT}:{self._ctx.step.slug}", None)

        answers = get_answers(state)
        answers[output_key] = None
        set_answers(state, answers)

        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.STEP_COMPLETED,
            slug=self._ctx.step.slug,
            step_index=self._ctx.step_index,
            step_kind="resource",
            resource_ref=self._ctx.step.resource_ref,
            output_key=output_key,
            recovery=recovery,
            resource_error=detail,
            resource_remediation=remediation,
        )
        return PatternStatus.SUCCESS

    def _fail_step(
        self,
        state: BaseState,
        *,
        message: str | None = None,
        remediation: str | None = None,
        trace_dict: dict[str, Any] | None = None,
    ) -> PatternStatus:
        detail, resolved_trace, resolved_remediation = self._failure_context(state, message=message)
        trace = trace_dict if trace_dict is not None else resolved_trace
        hint = remediation if remediation is not None else resolved_remediation
        state.set(
            WizardKeys.RESOURCE_FEEDBACK,
            format_resource_feedback(
                self._ctx.step,
                resource_id=str(trace.get("resource_id")) if trace.get("resource_id") else None,
                provider=str(trace.get("provider")) if trace.get("provider") else None,
                action=str(trace.get("action") or self._ctx.step.resource_action or "invoke"),
                success=False,
                error=detail,
            ),
        )
        prompt_bundle = self._prompt_bundle(state)
        prompt_bundle["resource_error"] = detail
        if hint:
            prompt_bundle["resource_remediation"] = hint
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
            resource_remediation=hint,
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
            self._ctx.step.resource_action or trace.get("action")
            if isinstance(trace, dict)
            else None
        )
        action_label = action or "invoke"
        return f"Resource {self._ctx.step.resource_ref!r} (action={action_label}) failed"


def build_resource_phase(ctx: WizardPhaseContext) -> WizardResourceLeaf:
    return WizardResourceLeaf(ctx)
