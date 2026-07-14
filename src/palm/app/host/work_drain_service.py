"""Drain WorkIntents when the host is able (Android-shaped deferred work)."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any, Callable

from palm.common.triggers.registry import TriggerRegistry
from palm.common.work.schedule import ScheduleRegistry
from palm.common.work.store import WorkIntentStore
from palm.core.event import Event
from palm.core.work import WorkIntent

if TYPE_CHECKING:
    from palm.core.event import EventEngine
    from palm.core.storage import StorageEngine


class WorkDrainService:
    """Claim due intents and run flows via a submit callback.

    Default is explicit :meth:`tick` (run-when-able). Optional
    :meth:`start_background` polls like the outbox service (0.40.2).
    """

    def __init__(
        self,
        storage: StorageEngine,
        *,
        submit_flow: Callable[[str, dict[str, Any]], Any],
        event_engine: EventEngine | None = None,
        able: Callable[[], bool] | None = None,
        max_depth: int = 8,
        poll_interval: float = 1.0,
        batch_size: int = 10,
    ) -> None:
        self._store = WorkIntentStore(storage)
        self._schedules = ScheduleRegistry(storage, self._store)
        self._submit_flow = submit_flow
        self._event_engine = event_engine
        self._able = able or (lambda: True)
        self._max_depth = max(1, int(max_depth))
        self._poll_interval = max(0.05, float(poll_interval))
        self._batch_size = max(1, int(batch_size))
        self._triggers = TriggerRegistry()
        self._sub = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._bg_started = False
        self._dropped_depth = 0

    @property
    def store(self) -> WorkIntentStore:
        return self._store

    @property
    def schedules(self) -> ScheduleRegistry:
        return self._schedules

    @property
    def triggers(self) -> TriggerRegistry:
        return self._triggers

    @property
    def max_depth(self) -> int:
        return self._max_depth

    @property
    def dropped_depth_count(self) -> int:
        """Intents refused for exceeding max_depth (storm / loop guard)."""
        return self._dropped_depth

    @property
    def is_running(self) -> bool:
        return (
            self._bg_started
            and self._thread is not None
            and self._thread.is_alive()
        )

    def attach_events(self, event_engine: EventEngine) -> None:
        self._event_engine = event_engine
        if self._sub is not None:
            return
        self._sub = event_engine.subscribe("resource.changed", self._on_resource_event)
        event_engine.subscribe("flow.session.succeeded", self._on_flow_event)

    def reload_triggers(
        self,
        flow_rows: list[dict[str, Any]],
        *,
        get_metadata: Any = None,
    ) -> int:
        n = self._triggers.reload_from_flow_rows(
            flow_rows, get_metadata=get_metadata
        )
        # Durable schedules (0.41) — next_fire survives restart
        self._schedules.load_from_flow_rows(flow_rows, get_metadata=get_metadata)
        return n

    def enqueue(self, intent: WorkIntent) -> str:
        if intent.depth > self._max_depth:
            self._dropped_depth += 1
            return ""
        return self._store.enqueue(intent)

    def tick_schedules(self) -> int:
        """Fire durable interval schedules into the work queue."""
        return len(self._schedules.tick(limit=self._batch_size))

    def tick(self, *, limit: int | None = None) -> int:
        """Claim and execute due work. Returns number of intents processed."""
        if not self._able():
            return 0
        batch = self._batch_size if limit is None else max(1, int(limit))
        claimed = self._store.claim_due(limit=batch)
        done = 0
        for intent in claimed:
            try:
                if intent.kind == "run_flow":
                    self._submit_flow(intent.target, dict(intent.payload))
                else:
                    raise ValueError(f"unsupported work kind {intent.kind!r}")
                self._store.ack(intent.id)
                done += 1
            except Exception as exc:  # noqa: BLE001
                self._store.fail(intent.id, str(exc))
        return done

    def start_background(self) -> None:
        """Optional continuous drain loop (PALM_ENABLE_WORK_DRAIN_SERVICE)."""
        if self._bg_started:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._poll_loop,
            name="palm-work-drain",
            daemon=True,
        )
        self._thread.start()
        self._bg_started = True

    def stop_background(self, *, timeout: float = 2.0) -> None:
        if not self._bg_started:
            return
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self._thread = None
        self._bg_started = False

    def _poll_loop(self) -> None:
        while not self._stop.wait(self._poll_interval):
            try:
                if not self._able():
                    continue
                self.tick_schedules()
                self.tick(limit=self._batch_size)
            except Exception:
                continue

    def _on_resource_event(self, event: Event) -> None:
        payload = event.enriched_payload() if hasattr(event, "enriched_payload") else dict(
            event.payload or {}
        )
        for intent in self._triggers.on_event(event.type, payload):
            self.enqueue(intent)

    def _on_flow_event(self, event: Event) -> None:
        payload = event.enriched_payload() if hasattr(event, "enriched_payload") else dict(
            event.payload or {}
        )
        for intent in self._triggers.on_event(event.type, payload):
            self.enqueue(intent)


__all__ = ["WorkDrainService"]
