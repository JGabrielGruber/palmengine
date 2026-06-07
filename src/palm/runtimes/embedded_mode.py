"""
EmbeddedMode — synchronous in-process orchestration for :class:`~palm.runtimes.embedded.EmbeddedRuntime`.

Drives jobs immediately in the caller thread using a pluggable
:class:`~palm.core.orchestration.execution.base_runner.JobRunner`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.orchestration.execution.base_runner import JobRunner
from palm.core.orchestration.job import JobStatus
from palm.core.orchestration.mode.base_mode import OrchestrationMode

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job


class EmbeddedMode(OrchestrationMode):
    """Runs jobs synchronously in the caller thread using an external runner."""

    def __init__(
        self,
        *,
        backend: JobRunner,
        name: str = "EmbeddedMode",
    ) -> None:
        super().__init__(name=name)
        self._runner = backend
        self._running = False

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

    def _drive_job(self, engine: OrchestrationEngine, job: Job) -> None:
        result = self._runner.run(engine.execution_context(job), budget=10_000)
        engine.apply_result(job, result)