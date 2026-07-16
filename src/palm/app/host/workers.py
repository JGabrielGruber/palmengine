"""
Worker coordination — readiness tracking for multi-runtime hosts.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

from palm.app.host.events import HostEventType
from palm.app.host.roles import DeploymentProfile
from palm.core.event import EventEngine

if TYPE_CHECKING:
    from palm.app.app import PalmApp


class WorkerCoordinator:
    """
    Tracks worker runtime registration and signals readiness to the host bus.

    Used during startup recovery when master and worker roles share a process or
    storage-backed cluster.
    """

    def __init__(
        self,
        profile: DeploymentProfile,
        event_engine: EventEngine,
    ) -> None:
        self._profile = profile
        self._event_engine = event_engine
        self._registered: set[str] = set()
        self._lock = threading.RLock()
        self._ready_emitted = False

    @property
    def expected_workers(self) -> int:
        if self._profile.uses_collapsed_runtime:
            return 1
        if not self._profile.worker and not self._profile.server:
            return 0
        if self._profile.server and not self._profile.worker:
            return 1
        return self._profile.worker_count

    @property
    def registered_workers(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._registered))

    def note_runtime(self, name: str, kind: str) -> None:
        """Record a worker-capable runtime registration."""
        worker_kinds = {"daemon", "server"}
        if self._profile.uses_collapsed_runtime:
            worker_kinds.add("embedded")
        if kind not in worker_kinds:
            return
        with self._lock:
            self._registered.add(name)

    def wait_until_ready(self, app: PalmApp, *, timeout: float = 5.0) -> bool:
        """
        Block until expected worker runtimes are registered or ``timeout`` elapses.

        Returns ``True`` when all expected workers registered, else ``False``.
        """
        expected = self.expected_workers
        if expected == 0:
            self._emit_ready(expected=0, registered=())
            return True

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if len(self._registered) >= expected:
                    self._emit_ready(expected=expected, registered=self.registered_workers)
                    return True
            self._sync_from_app(app)
            time.sleep(0.05)

        with self._lock:
            registered = self.registered_workers
        self._emit_ready(expected=expected, registered=registered, timed_out=True)
        return len(registered) >= expected

    def _sync_from_app(self, app: PalmApp) -> None:
        for name in app.running():
            handle = app._runtimes.get(name)
            if handle is None or not handle.is_started:
                continue
            kind = handle.runtime.__class__.__name__.replace("Runtime", "").lower()
            worker_kinds = {"daemon", "server"}
            if self._profile.uses_collapsed_runtime:
                worker_kinds.add("embedded")
            if kind in worker_kinds:
                with self._lock:
                    self._registered.add(name)

    def _emit_ready(
        self,
        *,
        expected: int,
        registered: tuple[str, ...],
        timed_out: bool = False,
    ) -> None:
        with self._lock:
            if self._ready_emitted:
                return
            self._ready_emitted = True
        self._event_engine.emit(
            HostEventType.WORKERS_READY,
            expected=expected,
            registered=list(registered),
            timed_out=timed_out,
        )
