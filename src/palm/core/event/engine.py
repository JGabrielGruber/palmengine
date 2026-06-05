"""
Event engine — publish/subscribe observability bus.

Synchronous, in-memory event dispatch for engines and runtimes. Replaceable
with async or external buses at the runtime layer.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from palm.core.base import BasePalmEngine

EventHandler = Callable[["Event"], None]


@dataclass(frozen=True)
class Event:
    """Immutable domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventEngine(BasePalmEngine):
    """Minimal synchronous event bus."""

    def __init__(self) -> None:
        super().__init__(name="event")
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers.get(event.type, []):
            handler(event)
        for handler in self._handlers.get("*", []):
            handler(event)

    def emit(self, event_type: str, **payload: Any) -> None:
        self.publish(Event(type=event_type, payload=payload))

    def _do_initialize(self, **options: Any) -> None:
        pass

    def _do_shutdown(self) -> None:
        self._handlers.clear()
