"""
Runtime router — command-side worker selection for ApplicationHost.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.app.kernel import PalmKernel
    from palm.app.registry import RuntimeHandle


class RuntimeRouter:
    """
    Select orchestration runtimes for job-driving commands.

    Queries and master-only operations use the primary runtime. Submit/resume
    commands round-robin across worker runtimes when available.
    """

    def __init__(self, app: PalmKernel) -> None:
        self._app = app
        self._lock = threading.Lock()
        self._worker_index = 0

    def primary_runtime_name(self) -> str | None:
        return self._app.primary_name

    def worker_runtime_names(self) -> list[str]:
        workers: list[str] = []
        for handle in self._ordered_handles():
            if self._is_worker_handle(handle):
                workers.append(handle.name)
        return workers

    def route_job_runtime(self, explicit: str | None = None) -> str | None:
        """Resolve the runtime that should execute a job-driving command."""
        if explicit is not None:
            return explicit
        workers = self.worker_runtime_names()
        if not workers:
            return None
        if len(workers) == 1:
            return workers[0]
        with self._lock:
            name = workers[self._worker_index % len(workers)]
            self._worker_index += 1
        return name

    def _ordered_handles(self) -> list[RuntimeHandle]:
        return list(self._app._runtimes.items())

    @staticmethod
    def _is_worker_handle(handle: RuntimeHandle) -> bool:
        if handle.kind == "daemon":
            return True
        if handle.kind == "server":
            return True
        return False
