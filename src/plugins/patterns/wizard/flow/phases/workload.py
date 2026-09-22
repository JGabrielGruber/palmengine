"""Workload phase — declarative WorkloadLeaf invocation inside a wizard step."""

from __future__ import annotations

from palm.system.subsystems.planes.workload.run_python import spec_from_bound_params
from palm.core.resource.invocation import bind_resource_params
from palm.core.behavior_tree import LeafNode, PatternStatus, WorkloadLeaf
from palm.core.context import BaseState
from palm.core.workload.owner import WorkloadOwner
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
from plugins.patterns.wizard.flow.phases._base import WizardPhaseContext, wizard_prompt_key
from plugins.patterns.wizard.flow.validation import (
    clear_validation_feedback,
    publish_validation_feedback,
)


def default_workload_prompt(step: WizardStepConfig) -> str:
    target = step.output_key or step.slug
    return f"Running workload → {target}"


def build_workload_phase(ctx: WizardPhaseContext) -> LeafNode:
    return WizardWorkloadLeaf(ctx)


class WizardWorkloadLeaf(LeafNode):
    """Bind step params → WorkloadSpec → WorkloadEngine (via WorkloadLeaf)."""

    def __init__(self, ctx: WizardPhaseContext) -> None:
        step = ctx.step
        super().__init__(step.slug)
        if step.step_kind != "workload":
            raise ValueError(
                f"WizardWorkloadLeaf requires step_kind=workload, got {step.step_kind!r}"
            )
        if not step.params:
            raise ValueError(
                f"Workload step {step.slug!r} requires params "
                "(WorkloadSpec fields or run-python sugar: code/runtime)"
            )
        self._ctx = ctx
        self._output_key = step.output_key or step.slug
        self._error_key = f"{WizardKeys.PREFIX}.workload_error:{step.slug}"
        self._inner: WorkloadLeaf | None = None
        self._started = False

    def prompt_key(self) -> str:
        return wizard_prompt_key(self._ctx.step.slug)

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        enter_wizard_step(
            state,
            self._ctx.step,
            index=self._ctx.step_index,
            context=self._ctx.context_engine,
        )

        prompt_bundle = build_prompt_bundle(
            state,
            wizard_name=self._ctx.wizard_name,
            step=self._ctx.step,
            step_index=self._ctx.step_index,
            context=self._ctx.context_engine,
            include_validation=False,
            prompt=self._ctx.step.prompt or default_workload_prompt(self._ctx.step),
            field_type="workload",
            auto_advance=True,
            output_key=self._output_key,
        )
        publish_prompt(state, prompt_key=self.prompt_key(), bundle=prompt_bundle)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.STEP_STARTED,
            slug=self._ctx.step.slug,
            title=self._ctx.step.title,
            step_index=self._ctx.step_index,
            step_kind="workload",
        )

        self._promote_answers_for_binding(state)

        try:
            if self._inner is None:
                self._inner = self._build_inner(state)
            status = self._inner.tick(state)
        except Exception as exc:
            return self._fail(state, str(exc))

        if status == PatternStatus.RUNNING:
            return PatternStatus.RUNNING

        if status == PatternStatus.SUCCESS:
            return self._complete_success(state)

        err = state.get(self._error_key) or state.get(self._inner.trace_key if self._inner else "")
        message = str(err) if err else "Workload step failed"
        if isinstance(err, dict) and err.get("error"):
            message = str(err["error"])
        return self._fail(state, message)

    def _build_inner(self, state: BaseState) -> WorkloadLeaf:
        engine = self._ctx.workload_engine
        if engine is None:
            raise RuntimeError(
                "WorkloadEngine is not configured on wizard "
                "(runtime.workload must be started)"
            )
        bound = bind_resource_params(self._ctx.step.params, state)
        spec = spec_from_bound_params(bound)
        owner = WorkloadOwner(
            job_id=str(state.get("job_id") or "") or None,
            session_id=str(state.get("session_id") or "") or None,
        )
        # Prefer orchestration job id when present on state
        meta_job = state.get("__job_id__") or state.get("palm.job_id")
        if meta_job and not owner.job_id:
            owner = WorkloadOwner(job_id=str(meta_job), session_id=owner.session_id)

        return WorkloadLeaf(
            self._ctx.step.slug,
            workload_engine=engine,
            spec=spec,
            owner=owner,
            output_key=self._output_key,
            error_key=self._error_key,
        )

    def _promote_answers_for_binding(self, state: BaseState) -> None:
        answers = get_answers(state)
        if not isinstance(answers, dict):
            return
        for key, value in answers.items():
            if not state.has(str(key)):
                state.set(str(key), value)

    def _complete_success(self, state: BaseState) -> PatternStatus:
        step = self._ctx.step
        clear_validation_feedback(state)
        clear_active_prompt(state)
        # Flatten useful fields for later transform/display steps
        payload = state.get(self._output_key)
        answers = dict(get_answers(state) or {})
        if isinstance(payload, dict):
            answers[self._output_key] = payload
            result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
            if result:
                stdout = result.get("stdout_tail") or ""
                exit_code = result.get("exit_code")
                state.set("stdout", stdout)
                if exit_code is not None:
                    state.set("exit_code", exit_code)
                answers["stdout"] = stdout
                if exit_code is not None:
                    answers["exit_code"] = exit_code
        set_answers(state, answers)

        leave_wizard_step(state, step, context=self._ctx.context_engine)
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.STEP_COMPLETED,
            slug=step.slug,
            title=step.title,
            step_index=self._ctx.step_index,
            step_kind="workload",
        )
        return PatternStatus.SUCCESS

    def _fail(self, state: BaseState, message: str) -> PatternStatus:
        step = self._ctx.step
        detail = f"Workload step {step.slug!r} failed: {message}"
        state.set(self._error_key, detail)
        publish_validation_feedback(state, step.slug, [detail])
        emit_wizard_event(
            self._ctx.emit,
            self._ctx.wizard_name,
            WizardEventType.VALIDATION_FAILED,
            slug=step.slug,
            step_index=self._ctx.step_index,
            step_kind="workload",
            error=message,
        )
        return PatternStatus.FAILURE


__all__ = ["WizardWorkloadLeaf", "build_workload_phase", "default_workload_prompt"]
