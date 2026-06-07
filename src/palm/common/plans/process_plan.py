"""
ProcessPlan — orchestration-ready bundle for multi-flow process definitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.common.plans.execution_plan import ExecutionPlan
from palm.definitions.process import ProcessDefinition

if TYPE_CHECKING:
    from palm.core.orchestration import Job, OrchestrationEngine


@dataclass(frozen=True)
class ProcessPlan:
    """
    Orchestration-ready bundle for a multi-flow process definition.

    Each flow becomes an :class:`~palm.common.plans.execution_plan.ExecutionPlan`. Submit
    individually for fine-grained control, or use :meth:`submit_all` for the
    full batch.
    """

    process: ProcessDefinition
    plans: tuple[ExecutionPlan, ...]

    def submit_all(self, orchestration: OrchestrationEngine) -> list[Job]:
        """Register every plan in process order."""
        return [plan.submit_to(orchestration) for plan in self.plans]
