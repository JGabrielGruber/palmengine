"""
Daemon runtime — long-lived background Palm process.
"""

from __future__ import annotations

import signal
import threading
from typing import Any, ClassVar

from palm.runtimes.base import BaseRuntime
from palm.runtimes.schedulers import QueuedScheduler
from palm.runtimes.wiring import SchedulerPolicy


class DaemonRuntime(BaseRuntime):
    """
    Long-lived runtime with background job driving by default.

    Uses :class:`~palm.runtimes.schedulers.queued.QueuedScheduler` so callers
    return immediately after submission while a worker thread advances jobs.
    """

    runtime_name: ClassVar[str] = "DaemonRuntime"
    default_scheduler_policy: ClassVar[SchedulerPolicy] = "queued"

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        """
        Block until the background scheduler has processed queued work.

        Convenience for tests and coordinated shutdown; observe job status via
        orchestration for production completion tracking.
        """
        self._require_started()
        scheduler = self.orchestration.scheduler
        if isinstance(scheduler, QueuedScheduler):
            return scheduler.wait_until_idle(timeout=timeout)
        return True


def run_daemon(**options: Any) -> None:
    """
    Start a daemon runtime and block until interrupted by SIGINT/SIGTERM.

    Options are forwarded to :meth:`DaemonRuntime.start` (e.g. ``storage``,
    ``scheduler``, ``hooks``).
    """
    storage = options.pop("storage", None)
    runtime = DaemonRuntime(storage=storage)
    runtime.start(**options)

    stopped = threading.Event()

    def _stop(*_: object) -> None:
        stopped.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    stopped.wait()
    runtime.stop()