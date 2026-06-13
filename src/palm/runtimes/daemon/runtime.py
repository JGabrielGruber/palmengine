"""
Daemon runtime — long-lived background Palm process.
"""

from __future__ import annotations

import signal
import threading
from typing import Any, ClassVar

from palm.common.runtimes.base import BaseRuntime
from palm.common.runtimes.wiring import SchedulerPolicy


class DaemonRuntime(BaseRuntime):
    """
    Long-lived runtime with background job driving by default.

    Uses :class:`~palm.common.runtimes.schedulers.queued.QueuedScheduler` so callers
    return immediately after submission while a worker thread advances jobs.
    """

    runtime_name: ClassVar[str] = "DaemonRuntime"
    default_scheduler_policy: ClassVar[SchedulerPolicy] = "queued"


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
