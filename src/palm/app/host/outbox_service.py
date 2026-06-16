"""
Outbox background service — periodic drain for master-role hosts.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from palm.common.events import OutboxProcessor, OutboxStore, wire_reliable_events
from palm.core.event import EventEngine

if TYPE_CHECKING:
    from palm.core.storage import StorageEngine


class OutboxBackgroundService:
    """
    Polls the shared outbox and marks entries published.

    Runs on master-role hosts. Uses a dedicated host-level
    :class:`~palm.core.event.EventEngine` for recovery replay and observability.
    """

    def __init__(
        self,
        storage: StorageEngine,
        event_engine: EventEngine,
        *,
        poll_interval: float = 0.5,
        batch_size: int = 50,
    ) -> None:
        self._storage = storage
        self._event_engine = event_engine
        self._poll_interval = poll_interval
        self._batch_size = batch_size
        self._store = OutboxStore(storage)
        self._processor = OutboxProcessor(self._store, event_engine)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._started = False

    @property
    def store(self) -> OutboxStore:
        return self._store

    @property
    def processor(self) -> OutboxProcessor:
        return self._processor

    @property
    def is_running(self) -> bool:
        return self._started and self._thread is not None and self._thread.is_alive()

    def start(self, *, recover: bool = True) -> None:
        if self._started:
            return
        if not self._event_engine.is_initialized:
            self._event_engine.initialize()
        wire_reliable_events(self._event_engine, self._store)
        if recover:
            self._processor.recover_pending(replay_handlers=False)
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._poll_loop,
            name="palm-outbox",
            daemon=True,
        )
        self._thread.start()
        self._started = True

    def stop(self, *, timeout: float = 2.0) -> None:
        if not self._started:
            return
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self._thread = None
        self._started = False

    def process_once(self) -> int:
        """Process a single batch — useful in tests."""
        return self._processor.process_batch(limit=self._batch_size)

    def _poll_loop(self) -> None:
        while not self._stop.wait(self._poll_interval):
            try:
                count = self._processor.process_batch(limit=self._batch_size)
                if count:
                    self._event_engine.emit(
                        "host.outbox.processed",
                        count=count,
                        pending=self._store.pending_count(),
                    )
            except Exception:
                continue