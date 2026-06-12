"""
InlineScheduler — synchronous in-process job scheduling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.orchestration.drive import drive_job
from palm.core.orchestration.execution.base_runner import JobRunner
from palm.core.orchestration.job import JobStatus
from palm.core.orchestration.mode.base_mode import OrchestrationMode

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job


class InlineScheduler(OrchestrationMode):
    """
    Runs jobs synchronously in the caller thread using a :class:`~palm.core.orchestration.execution.base_runner.JobRunner`.

    This is the default scheduler for :class:`~palm.runtimes.embedded.EmbeddedRuntime`.
    """

    def __init__(
        self,
        *,
        runner: JobRunner,
        budget: int = 10_000,
        name: str = "InlineScheduler",
    ) -> None:
        super().__init__(name=name)
        self._runner = runner
        self._budget = budget
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
        self._drive(engine, job)

    def resume_job(self, engine: OrchestrationEngine, job: Job) -> None:
        if job.status == JobStatus.WAITING_FOR_INPUT:
            self._drive(engine, job)

    def _drive(self, engine: OrchestrationEngine, job: Job) -> None:
        drive_job(engine, self._runner, job, budget=self._budget)
