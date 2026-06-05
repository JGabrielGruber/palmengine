"""
ExecutionBackend — abstract base for pluggable strategies that advance Jobs.

This is the lower-level Strategy (composed inside `OrchestrationMode`) that
defines *how* a particular `job.executable` makes progress.

Design goals for the core:
- The `Orchestrator` and `Job` are completely agnostic about execution details.
- Only the abstract contract lives in `palm/core/orchestration/`.
- The **only** concrete backend that may live inside this package is `TestBackend`
  (see `test_backend.py`). All other concrete backends (Behavior Trees,
  subprocesses, remote workers, etc.) live outside `palm/core/` (typically under
  `palm/backends/` or domain-specific packages).

This module (and the whole `palm/core/orchestration/` tree) must remain
completely independent of the Behavior Tree Engine and any domain code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..job import Job, JobStatus


class ExecutionBackend(ABC):
    """
    Abstract strategy for advancing executable work associated with a Job.

    Implementations are responsible for:
    - Interpreting `job.executable` (opaque to the rest of the engine).
    - Driving the job through valid status transitions via the internal
      `_transition_to` helper (temporarily enabling mutation).
    - Returning the status reached after the advance attempt.
    - Respecting `max_steps` guards for safety in test / long-running scenarios.

    Concrete implementations:
        - `TestBackend` (in this package, the default for all core tests)
        - `BehaviorTreeBackend` (in `palm/backends/behavior_tree.py`)
        - Future: process backends, async backends, remote execution, etc.
    """

    @abstractmethod
    def advance(self, job: Job, *, max_steps: int | None = None) -> JobStatus:
        """
        Make progress on the job (one or more logical steps).

        The backend may transition the job through RUNNING, WAITING_FOR_INPUT,
        SUCCEEDED, FAILED, CANCELLED, etc. It must never leave the job in an
        inconsistent state.

        Returns the status after this drive.
        """
        ...
