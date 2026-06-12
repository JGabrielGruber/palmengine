"""
ExecutionPlan — orchestration-ready payload produced by the executions layer.

Separates *preparation* (definitions → executable + state + metadata) from
*submission* (registering a job with orchestration).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.common.exceptions import PlanValidationError
from palm.core.context import BaseState

if TYPE_CHECKING:
    from palm.core.orchestration import Job, OrchestrationEngine


@dataclass(frozen=True)
class ExecutionPlan:
    """
    Immutable description of work ready for orchestration.

    Produced by :func:`~palm.common.executions.flow_submission.prepare_flow_submission`
    and consumed by :meth:`~palm.common.executions.executor.DefinitionExecutor.submit_plan`
    or :meth:`submit_to`.
    """

    executable: Any
    state: BaseState
    metadata: dict[str, Any]
    job_id: str | None = None

    def validate(self) -> None:
        """
        Fail fast before orchestration submission.

        Lightweight structural checks only — pattern/build validation happens
        during preparation.
        """
        if self.executable is None:
            raise PlanValidationError("ExecutionPlan.executable must not be None")
        if not isinstance(self.state, BaseState):
            raise PlanValidationError("ExecutionPlan.state must be a BaseState")
        if not isinstance(self.metadata, dict):
            raise PlanValidationError("ExecutionPlan.metadata must be a dict")
        if self.job_id is not None and not str(self.job_id).strip():
            raise PlanValidationError("ExecutionPlan.job_id must be a non-empty string when set")

    def submit_to(self, orchestration: OrchestrationEngine) -> Job:
        """Register this plan as a job on an orchestration engine."""
        self.validate()
        return orchestration.submit(
            self.executable,
            state=self.state,
            job_id=self.job_id,
            metadata=self.metadata,
        )
