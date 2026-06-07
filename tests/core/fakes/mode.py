"""
TestMode — synchronous orchestration scheduler for unit tests.

Lives outside ``palm.core`` to preserve core purity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.orchestration.execution.base_runner import JobRunner
from palm.core.orchestration.job import JobStatus
from palm.core.orchestration.mode.base_mode import OrchestrationMode
from palm.core.orchestration.run_result import RunResult
from tests.core.fakes.backend import TestBackend

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job


class TestMode(OrchestrationMode):
    """Runs jobs synchronously in the caller thread using a runner."""

    __test__ = False

    def __init__(
        self,
        *,
        backend: JobRunner | None = None,
        name: str = "TestMode",
    ) -> None:
        super().__init__(name=name)
        self._runner: JobRunner = backend or TestBackend()
        self._running = False
        self._force_next_status: dict[str, JobStatus] = {}

    @property
    def runner(self) -> JobRunner:
        return self._runner

    def start(self) -> None:
        self._running = True

    def shutdown(self, *, timeout: float = 5.0) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def submit_job(self, engine: OrchestrationEngine, job: Job) -> None:
        if not self._running:
            self.start()
        self._drive_job(engine, job)

    def resume_job(self, engine: OrchestrationEngine, job: Job) -> None:
        if job.status == JobStatus.WAITING_FOR_INPUT:
            self._drive_job(engine, job)

    def run_until_idle(self, engine: OrchestrationEngine) -> None:
        for job in list(engine.list_jobs()):
            if job.status == JobStatus.RUNNING:
                self._drive_job(engine, job)

    def force_job_status(self, job: Job, status: JobStatus) -> None:
        job.status = status

    def simulate_step(self, engine: OrchestrationEngine, job: Job) -> JobStatus:
        result = self._runner.run(engine.execution_context(job), budget=1)
        engine.apply_result(job, result)
        return job.status

    def _drive_job(self, engine: OrchestrationEngine, job: Job) -> None:
        if job.id in self._force_next_status:
            forced = self._force_next_status.pop(job.id)
            engine.apply_result(job, RunResult(status=forced))
            return

        result = self._runner.run(engine.execution_context(job), budget=10_000)
        engine.apply_result(job, result)