"""
JobRunner — abstract strategy for interpreting job executables.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from palm.core.orchestration.execution_context import ExecutionContext
from palm.core.orchestration.run_result import RunResult


class JobRunner(ABC):
    """Computes the next job status from an executable without mutating the job."""

    @abstractmethod
    def run(self, ctx: ExecutionContext, *, budget: int | None = None) -> RunResult:
        """Execute up to ``budget`` steps and return the desired job outcome."""
