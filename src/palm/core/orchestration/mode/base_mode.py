"""
OrchestrationMode — strategy for how jobs are driven at runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from palm.core.orchestration.job import JobStatus

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job


class OrchestrationMode(ABC):
    """Controls when and how submitted jobs make progress."""

    def __init__(self, name: str | None = None) -> None:
        self.name: str = name or self.__class__.__name__

    @abstractmethod
    def start(self) -> None:
        """Prepare the mode for accepting work."""

    @abstractmethod
    def shutdown(self, *, timeout: float = 5.0) -> None:
        """Stop background activity and release resources."""

    @abstractmethod
    def is_running(self) -> bool:
        """Return whether the mode can accept and advance jobs."""

    def submit_job(self, engine: OrchestrationEngine, job: Job) -> None:
        """Called after a job is registered."""
        return None

    def resume_job(self, engine: OrchestrationEngine, job: Job) -> None:
        """Called after input is supplied to a waiting job."""
        return None

    def cancel_job(self, engine: OrchestrationEngine, job: Job) -> None:
        if not job.is_terminal:
            job._allow_mutation = True
            try:
                job._transition_to(JobStatus.CANCELLED)
            finally:
                job._allow_mutation = False

    def on_engine_shutdown(self, engine: OrchestrationEngine) -> None:
        """Final hook before the engine finishes shutdown."""
        return None
