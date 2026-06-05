"""
Palm Core Events — lightweight, general-purpose in-memory event bus.

This module provides the shared observability primitive used by all
general-purpose engines in `palm.core` (Behavior Tree Engine, Orchestration
Engine, and any future engines).

It is intentionally minimal, synchronous, and dependency-free (stdlib only).
Higher layers (orchestrator modes, external adapters) can replace it with
Redis/NATS/etc. without changing the core engine contracts.

This module must remain completely independent of wizards, CLI, RichContext,
persistence, and any domain-specific code.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Event:
    """
    A lightweight, immutable domain event emitted by core engines.

    Attributes:
        name: Human/machine readable event name (e.g. "job.status_changed").
        payload: Arbitrary serializable data. Keep small.
        timestamp: UTC timestamp of emission (set automatically).
        id: Unique identifier (UUID4 string, set automatically).
    """

    name: str
    payload: dict[str, Any]
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
        compare=False,
    )
    id: str = field(
        default_factory=lambda: str(uuid.uuid4()),
        compare=False,
    )

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Event name must be a non-empty string")


class EventBus:
    """
    Simple synchronous in-memory event bus.

    Design principles (matching Palm core philosophy):
    - All engines publish through this bus for observability.
    - Handlers are called synchronously in registration order.
    - Individual handler exceptions are isolated (logged + swallowed) so one
      bad subscriber never breaks the publisher or other subscribers.
    - Supports subscribe + unsubscribe for clean test teardown.
    - Not thread-safe by design. Higher layers (Orchestrator modes) that
      introduce concurrency are responsible for serialization.

    Typical usage:
        bus = EventBus()
        events: list[Event] = []
        bus.subscribe("job.completed", events.append)
        bus.publish_named("job.completed", {"job_id": "abc", "status": "SUCCEEDED"})
        assert len(events) == 1
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[Event], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        """Register a handler for the given event name. Idempotent per (name, handler)."""
        if not event_name or not isinstance(event_name, str):
            raise ValueError("event_name must be a non-empty string")
        if handler is None:
            raise ValueError("handler must be a callable")
        handlers = self._handlers.setdefault(event_name, [])
        if handler not in handlers:
            handlers.append(handler)

    def unsubscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        """Remove a previously registered handler. Safe if not present."""
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
            except ValueError:
                pass  # not subscribed
            if not self._handlers[event_name]:
                del self._handlers[event_name]

    def publish(self, event: Event) -> None:
        """
        Deliver the event to all current subscribers for its name.

        Handler exceptions are caught individually and swallowed (future:
        could route to a dead-letter or logger). The bus itself never raises
        from publish due to a handler.
        """
        for handler in list(self._handlers.get(event.name, [])):
            try:
                handler(event)
            except Exception:
                # Defensive isolation — do not let one observer break the system.
                # In production a real logger would be used here.
                pass

    def publish_named(self, name: str, payload: dict[str, Any]) -> None:
        """Convenience: create and publish an Event in one call."""
        self.publish(Event(name=name, payload=payload))

    def __repr__(self) -> str:
        total = sum(len(h) for h in self._handlers.values())
        return f"EventBus(subscriptions={len(self._handlers)}, total_handlers={total})"
