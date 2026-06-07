"""
Process submission preparation — multi-flow definitions to execution plans.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.executions.flow_submission import prepare_flow_submission
from palm.common.plans.execution_plan import ExecutionPlan
from palm.common.plans.process_plan import ProcessPlan
from palm.definitions.process import ProcessDefinition

if TYPE_CHECKING:
    from typing import Any

    from palm.common.patterns.build_context import PatternBuildContext
    from palm.common.persistence.instance_repository import InstanceRepository
    from palm.core.context import BaseState


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
    """Build one :class:`~palm.common.plans.execution_plan.ExecutionPlan` per process flow."""
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
