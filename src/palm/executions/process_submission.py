"""
Process submission preparation — multi-flow definitions to execution plans.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.definitions.process import ProcessDefinition
from palm.executions.flow_submission import prepare_flow_submission
from palm.executions.plan import ExecutionPlan

if TYPE_CHECKING:
    from typing import Any

    from palm.core.context import BaseState
    from palm.core.orchestration import Job, OrchestrationEngine
    from palm.executions.build_context import PatternBuildContext
    from palm.executions.instance_repository import InstanceRepository


@dataclass(frozen=True)
class ProcessPlan:
    """
    Orchestration-ready bundle for a multi-flow process definition.

    Each flow becomes an :class:`~palm.executions.plan.ExecutionPlan`. Submit
    individually for fine-grained control, or use :meth:`submit_all` for the
    full batch.
    """

    process: ProcessDefinition
    plans: tuple[ExecutionPlan, ...]

    def submit_all(self, orchestration: OrchestrationEngine) -> list[Job]:
        """Register every plan in process order."""
        return [plan.submit_to(orchestration) for plan in self.plans]


def prepare_process_plans(
    process: ProcessDefinition,
    *,
    state: BaseState | None,
    metadata: dict[str, Any] | None,
    instances: InstanceRepository | None,
    build_ctx: PatternBuildContext,
    job_id: str | None = None,
    instance_id: str | None = None,
) -> ProcessPlan:
    """Build one :class:`~palm.executions.plan.ExecutionPlan` per process flow."""
    plans: list[ExecutionPlan] = []
    for index, flow in enumerate(process.flows):
        flow_meta = dict(metadata or {})
        flow_meta.setdefault("definition_type", "process")
        flow_meta.setdefault("process", process.name)
        flow_meta.setdefault("process_id", process.definition_id)
        flow_meta.setdefault("storage", process.storage)
        if process.metadata:
            flow_meta.setdefault("process_metadata", dict(process.metadata))

        assigned_id = job_id if index == 0 else None
        assigned_instance = instance_id if index == 0 else None
        submission = prepare_flow_submission(
            flow,
            state=state,
            metadata=flow_meta,
            instances=instances,
            build_ctx=build_ctx,
            instance_id=assigned_instance,
        )
        plans.append(submission.to_plan(job_id=assigned_id))

    return ProcessPlan(process=process, plans=tuple(plans))