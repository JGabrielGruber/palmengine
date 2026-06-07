"""
Flow submission preparation — definitions to orchestration-ready payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState
from palm.definitions.flow import FlowDefinition
from palm.executions.build_context import PatternBuildContext
from palm.executions.builder import build_pattern
from palm.executions.instance_sync import prepare_resume_state
from palm.executions.plan import ExecutionPlan
from palm.executions.wizard_options import wizard_metadata_from_flow
from palm.instances import ProcessInstance
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.executions.instance_repository import InstanceRepository


@dataclass(frozen=True)
class FlowSubmission:
    """Orchestration-ready product of a flow definition build."""

    flow: FlowDefinition
    executable: Any
    state: BaseState
    metadata: dict[str, Any]
    instance_id: str | None

    def to_plan(self, *, job_id: str | None = None) -> ExecutionPlan:
        """Convert this submission into an :class:`~palm.executions.plan.ExecutionPlan`."""
        return ExecutionPlan(
            executable=self.executable,
            state=self.state,
            metadata=self.metadata,
            job_id=job_id,
        )


def prepare_flow_submission(
    flow: FlowDefinition,
    *,
    state: BaseState | None,
    metadata: dict[str, Any] | None,
    instances: InstanceRepository | None,
    build_ctx: PatternBuildContext,
    instance_id: str | None = None,
) -> FlowSubmission:
    """Build a pattern executable and job metadata from a flow definition."""
    if flow.pattern == "wizard":
        build_ctx.wizard_metadata = wizard_metadata_from_flow(flow.options)

    executable = build_pattern(flow, context=build_ctx)
    job_state = state if state is not None else BlackboardState()
    meta = dict(metadata or {})
    meta.setdefault("definition_type", "flow")
    meta.setdefault("flow", flow.name)
    meta.setdefault("flow_id", flow.definition_id)
    meta.setdefault("pattern", flow.pattern)
    meta["flow_definition"] = flow.to_dict()
    if build_ctx.wizard_metadata:
        meta.setdefault("wizard", dict(build_ctx.wizard_metadata))

    iid = instance_id
    if iid is None and instances is not None:
        iid = instances.new_instance_id()
    if iid is not None:
        meta["instance_id"] = iid

    return FlowSubmission(
        flow=flow,
        executable=executable,
        state=job_state,
        metadata=meta,
        instance_id=iid,
    )


def prepare_resume_submission(
    instance: ProcessInstance,
    *,
    build_ctx: PatternBuildContext,
) -> FlowSubmission:
    """Rebuild a submission payload from a persisted process instance."""
    flow = FlowDefinition.from_dict(instance.flow_definition)
    if flow.pattern == "wizard":
        build_ctx.wizard_metadata = wizard_metadata_from_flow(flow.options)

    executable = build_pattern(flow, context=build_ctx)
    state = prepare_resume_state(instance, executable)
    meta = dict(instance.metadata)
    meta["instance_id"] = instance.instance_id
    meta["resumed"] = True
    meta["flow_definition"] = instance.flow_definition

    return FlowSubmission(
        flow=flow,
        executable=executable,
        state=state,
        metadata=meta,
        instance_id=instance.instance_id,
    )