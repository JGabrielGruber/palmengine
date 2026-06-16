"""
Host event recorder — ring buffer of recent host-level events for dashboards.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from palm.core.event import Event, EventEngine, Subscription


@dataclass(frozen=True)
class RecordedEvent:
    """Lightweight snapshot of a host bus event."""

    type: str
    timestamp: str
    payload: dict[str, Any]

    @classmethod
    def from_event(cls, event: Event) -> RecordedEvent:
        return cls(
            type=event.type,
            timestamp=event.timestamp.isoformat(),
            payload=dict(event.payload),
        )


class HostEventRecorder:
    """Retain the last N events emitted on the host coordination bus."""

    def __init__(self, *, capacity: int = 10) -> None:
        self._capacity = capacity
        self._events: deque[RecordedEvent] = deque(maxlen=capacity)
        self._subscription: Subscription | None = None

    @property
    def capacity(self) -> int:
        return self._capacity

    def attach(self, event_engine: EventEngine) -> Subscription:
        def record(event: Event) -> None:
            self._events.append(RecordedEvent.from_event(event))

        self._subscription = event_engine.subscribe("*", record)
        return self._subscription

    def recent(self, *, limit: int | None = None) -> list[RecordedEvent]:
        rows = list(self._events)
        if limit is not None:
            return rows[-limit:]
        return rows

    def shutdown(self) -> None:
        if self._subscription is not None:
            self._subscription.unsubscribe()
            self._subscription = None