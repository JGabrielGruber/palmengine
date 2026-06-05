"""
ExecutionBackend — abstract strategy for advancing job executables.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from palm.core.orchestration.job import Job, JobStatus


class ExecutionBackend(ABC):
    """Advances opaque ``job.executable`` work through valid job transitions."""

    @abstractmethod
    def advance(self, job: Job, *, max_steps: int | None = None) -> JobStatus:
        """Make progress on the job and return the resulting status."""
