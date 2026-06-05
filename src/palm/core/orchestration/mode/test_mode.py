"""
TestMode — synchronous orchestration mode for unit tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.orchestration.execution.base_backend import ExecutionBackend
from palm.core.orchestration.execution.test_backend import TestBackend
from palm.core.orchestration.job import JobStatus
from palm.core.orchestration.mode.base_mode import OrchestrationMode

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job


class TestMode(OrchestrationMode):
    """Runs jobs synchronously in the caller thread using a backend."""

    __test__ = False

    def __init__(
        self,
        *,
        backend: ExecutionBackend | None = None,
        name: str = "TestMode",
    ) -> None:
        super().__init__(name=name)
        self._backend: ExecutionBackend = backend or TestBackend()
        self._running = False
        self._force_next_status: dict[str, JobStatus] = {}

    def start(self) -> None:
        self._running = True

    def shutdown(self, *, timeout: float = 5.0) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def submit_job(self, engine: OrchestrationEngine, job: Job) -> None:
        if not self._running:
            self.start()
        self._drive_job(job)

    def resume_job(self, engine: OrchestrationEngine, job: Job) -> None:
        if job.status == JobStatus.WAITING_FOR_INPUT:
            self._drive_job(job)

    def run_until_idle(self, engine: OrchestrationEngine) -> None:
        for job in list(engine.list_jobs()):
            if job.status == JobStatus.RUNNING:
                self._drive_job(job)

    def force_job_status(self, job: Job, status: JobStatus) -> None:
        job.status = status

    def simulate_step(self, job: Job) -> JobStatus:
        job._allow_mutation = True
        try:
            return self._backend.advance(job, max_steps=1)
        finally:
            job._allow_mutation = False

    def _drive_job(self, job: Job) -> None:
        job._allow_mutation = True
        try:
            if job.id in self._force_next_status:
                forced = self._force_next_status.pop(job.id)
                job._transition_to(forced)
                return
            self._backend.advance(job, max_steps=10_000)
        finally:
            job._allow_mutation = False
