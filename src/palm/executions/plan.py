"""
ExecutionPlan — orchestration-ready payload produced by the executions layer.

Separates *preparation* (definitions → executable + state + metadata) from
*submission* (registering a job with orchestration).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState

if TYPE_CHECKING:
    from palm.core.orchestration import Job, OrchestrationEngine


@dataclass(frozen=True)
class ExecutionPlan:
    """
    Immutable description of work ready for orchestration.

    Produced by :func:`~palm.executions.flow_submission.prepare_flow_submission`
    and consumed by :meth:`~palm.executions.executor.DefinitionExecutor.submit_plan`
    or :meth:`submit_to`.
    """

    executable: Any
    state: BaseState
    metadata: dict[str, Any]
    job_id: str | None = None

    def submit_to(self, orchestration: OrchestrationEngine) -> Job:
        """Register this plan as a job on an orchestration engine."""
        return orchestration.submit(
            self.executable,
            state=self.state,
            job_id=self.job_id,
            metadata=self.metadata,
        )