"""
OrchestrationMode — the Strategy interface for different runtime execution models.

The Orchestrator accepts an OrchestrationMode at construction time and
delegates all lifecycle and job-execution decisions to it. This is the
core of the Strategy pattern that makes the engine open for extension
(EmbeddedMode, ProcessMode, distributed modes, TestMode, ...) while
remaining closed for modification.

This module is part of Palm's general-purpose Orchestration Engine and must
remain completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import Orchestrator
    from ..job import Job


class OrchestrationMode(ABC):
    """
    Abstract base for all execution strategies.

    Responsibilities:
    - Control when and how jobs actually make progress (synchronous vs background,
      thread-per-job, process isolation, etc.).
    - Implement graceful start / shutdown semantics.
    - Provide hooks that the Orchestrator calls at key moments
      (submit, input arrival, cancel, shutdown).

    Concrete modes own any background threads, schedulers, or worker pools.
    The Orchestrator itself stays free of concurrency primitives.
    """

    def __init__(self, name: str | None = None) -> None:
        self.name: str = name or self.__class__.__name__

    @abstractmethod
    def start(self) -> None:
        """Prepare the mode for work (start worker threads/loops if any)."""
        ...

    @abstractmethod
    def shutdown(self, *, timeout: float = 5.0) -> None:
        """
        Stop all background activity and release resources.

        Implementations should attempt to cancel or mark in-flight jobs as
        CANCELLED where possible. The caller (Orchestrator) is responsible for
        the final job state updates after this returns.
        """
        ...

    @abstractmethod
    def is_running(self) -> bool:
        """Return True if the mode is currently able to accept and advance jobs."""
        ...

    # ------------------------------------------------------------------
    # Extension points called by Orchestrator (override in subclasses)
    # ------------------------------------------------------------------

    def submit_job(self, orchestrator: Orchestrator, job: Job) -> None:
        """
        Called by Orchestrator.submit after the Job has been registered.

        Default implementation does nothing (useful for purely passive modes
        that only react to explicit drive calls from tests).
        """
        pass  # - intentional no-op extension point

    def resume_job(self, orchestrator: Orchestrator, job: Job) -> None:
        """
        Called after external input has been written to a WAITING job's blackboard.

        Default: no-op.
        """
        pass  # - intentional no-op extension point

    def cancel_job(self, orchestrator: Orchestrator, job: Job) -> None:
        """
        Best-effort cancellation hook.

        Default: mark the job CANCELLED if it is not already terminal.
        """
        if not job.is_terminal:
            job._allow_mutation = True
            try:
                job._transition_to("CANCELLED")  # type: ignore[arg-type]
            finally:
                job._allow_mutation = False

    def on_orchestrator_shutdown(self, orchestrator: Orchestrator) -> None:
        """
        Final notification just before the orchestrator finishes its own shutdown.

        Use for last-chance cleanup specific to this mode.
        """
        pass  # - intentional no-op extension point
