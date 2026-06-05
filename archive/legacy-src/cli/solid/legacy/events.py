"""
Lightweight event system for the Palm engine.

Useful for observability, metrics, and future distributed coordination.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Event:
    """A domain event emitted by the engine."""

    name: str
    payload: dict[str, Any]
    timestamp: datetime = field(
        default_factory=lambda: __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )
    )
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class EventBus:
    """
    In-memory synchronous event bus (sufficient for initial skeleton).

    For production daemon use, this can be replaced with Redis, NATS, etc.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[Event], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers.get(event.name, []):
            try:
                handler(event)
            except Exception:
                # In real system: log + dead letter
                pass

    def publish_named(self, name: str, payload: dict[str, Any]) -> None:
        self.publish(Event(name=name, payload=payload))
