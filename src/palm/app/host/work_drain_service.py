"""Drain WorkIntents when the host is able (Android-shaped deferred work)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Callable

from palm.common.triggers.registry import TriggerRegistry
from palm.common.work.store import WorkIntentStore
from palm.core.event import Event
from palm.core.work import WorkIntent

if TYPE_CHECKING:
    from palm.core.event import EventEngine
    from palm.core.storage import StorageEngine


class WorkDrainService:
    """Claim due intents and run flows via a submit callback."""

    def __init__(
        self,
        storage: StorageEngine,
        *,
        submit_flow: Callable[[str, dict[str, Any]], Any],
        event_engine: EventEngine | None = None,
        able: Callable[[], bool] | None = None,
        max_depth: int = 8,
    ) -> None:
        self._store = WorkIntentStore(storage)
        self._submit_flow = submit_flow
        self._event_engine = event_engine
        self._able = able or (lambda: True)
        self._max_depth = max_depth
        self._triggers = TriggerRegistry()
        self._sub = None

    @property
    def store(self) -> WorkIntentStore:
        return self._store

    @property
    def triggers(self) -> TriggerRegistry:
        return self._triggers

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
        return self._triggers.reload_from_flow_rows(
            flow_rows, get_metadata=get_metadata
        )

    def enqueue(self, intent: WorkIntent) -> str:
        if intent.depth > self._max_depth:
            return ""
        return self._store.enqueue(intent)

    def tick_schedules(self) -> int:
        intents = self._triggers.due_schedules(now_ts=time.time())
        for intent in intents:
            self.enqueue(intent)
        return len(intents)

    def tick(self, *, limit: int = 10) -> int:
        """Claim and execute due work. Returns number of intents processed."""
        if not self._able():
            return 0
        claimed = self._store.claim_due(limit=limit)
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
