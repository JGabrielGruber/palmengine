"""
Orchestration engine — job lifecycle and execution coordination.

Schedules and tracks work units with independent blackboard state. Stays
independent of the Behavior Tree engine and all domain code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from palm.core.base import BasePalmEngine


class JobStatus(Enum):
    """Lifecycle states for an orchestrated job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """A single unit of orchestrated work with its own blackboard."""

    name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.PENDING
    blackboard: dict[str, Any] = field(default_factory=dict)


class OrchestrationEngine(BasePalmEngine):
    """Creates, runs, and tracks jobs."""

    def __init__(self) -> None:
        super().__init__(name="orchestration")
        self._jobs: dict[str, Job] = {}

    @property
    def jobs(self) -> dict[str, Job]:
        return dict(self._jobs)

    def create_job(self, name: str) -> Job:
        job = Job(name=name)
        self._jobs[job.id] = job
        return job

    def run_job(self, job_id: str) -> JobStatus:
        job = self._jobs[job_id]
        job.status = JobStatus.RUNNING
        try:
            job.status = JobStatus.COMPLETED
        except Exception:
            job.status = JobStatus.FAILED
        return job.status

    def _do_initialize(self, **options: Any) -> None:
        pass

    def _do_shutdown(self) -> None:
        self._jobs.clear()
