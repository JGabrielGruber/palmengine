"""
QueuedScheduler — background-thread job scheduling via a work queue.

Runs jobs asynchronously in a dedicated worker thread while preserving the
canonical drive loop: ``JobRunner.run`` → ``RunResult`` → ``apply_result``.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.core.orchestration.drive import drive_job
from palm.core.orchestration.execution.base_runner import JobRunner
from palm.core.orchestration.job import JobStatus
from palm.core.orchestration.mode.base_mode import OrchestrationMode

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job

_SENTINEL = object()


@dataclass(frozen=True)
class _WorkItem:
    engine: OrchestrationEngine
    job: Job
    budget: int | None


class QueuedScheduler(OrchestrationMode):
    """
    Enqueue submitted and resumed jobs for a background worker to drive.

    Suitable for daemon and long-lived runtimes where callers should not block
    on pattern execution. For synchronous in-process use, prefer
    :class:`~palm.common.runtimes.schedulers.inline.InlineScheduler`.
    """

    def __init__(
        self,
        *,
        runner: JobRunner,
        budget: int = 10_000,
        name: str = "QueuedScheduler",
    ) -> None:
        if runner is None:
            raise TypeError("QueuedScheduler requires runner=")
        super().__init__(name=name)
        self._runner = runner
        self._budget = budget
        self._queue: queue.Queue[_WorkItem | object] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._running = False

    @property
    def runner(self) -> JobRunner:
        return self._runner

    def start(self) -> None:
        if self._running:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._worker,
            name=self.name,
            daemon=True,
        )
        self._thread.start()
        self._running = True

    def shutdown(self, *, timeout: float = 5.0) -> None:
        if not self._running:
            return
        self._stop.set()
        self._queue.put(_SENTINEL)
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)
        self._thread = None
        self._running = False

    def is_running(self) -> bool:
        return self._running and not self._stop.is_set()

    def submit_job(self, engine: OrchestrationEngine, job: Job) -> None:
        if not self._running:
            self.start()
        self._enqueue(engine, job)

    def resume_job(self, engine: OrchestrationEngine, job: Job) -> None:
        if job.status == JobStatus.WAITING_FOR_INPUT:
            self._enqueue(engine, job)

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        """
        Block until all queued work has been processed.

        Intended for tests and graceful shutdown coordination; not a general
        completion API for production callers.
        """
        deadline = time.monotonic() + timeout
        while self._queue.unfinished_tasks:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.01)
        return True

    def _enqueue(self, engine: OrchestrationEngine, job: Job) -> None:
        self._queue.put(_WorkItem(engine=engine, job=job, budget=self._budget))

    def _worker(self) -> None:
        while not self._stop.is_set():
            try:
                item = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if item is _SENTINEL:
                self._queue.task_done()
                break

            if not isinstance(item, _WorkItem):
                self._queue.task_done()
                continue

            work = item
            try:
                if not work.job.is_terminal:
                    drive_job(work.engine, self._runner, work.job, budget=work.budget)
            finally:
                self._queue.task_done()
