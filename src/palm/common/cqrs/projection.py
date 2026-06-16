"""
Projection framework — event-driven read model maintenance.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.core.event import Event, EventEngine


class Projection(ABC):
    """Maintains a read model by reacting to domain events."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable projection identifier."""

    @abstractmethod
    def handles(self, event_type: str) -> bool:
        """Return whether this projection consumes ``event_type``."""

    @abstractmethod
    def apply(self, event: Event) -> None:
        """Update the read model from ``event``."""

    @abstractmethod
    def rebuild(self) -> int:
        """Rebuild the read model from authoritative storage. Returns item count."""

    @abstractmethod
    def clear(self) -> None:
        """Remove the projection read model."""


class ProjectionManager:
    """Attach projections to event engines and coordinate rebuild."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._projections: list[Projection] = []
        self._subscriptions: list[tuple[EventEngine, object]] = []

    def register(self, projection: Projection) -> None:
        with self._lock:
            self._projections.append(projection)

    @property
    def projections(self) -> tuple[Projection, ...]:
        with self._lock:
            return tuple(self._projections)

    def attach(self, event_engine: EventEngine) -> None:
        """Subscribe all projections to ``event_engine``."""
        if not event_engine.is_initialized:
            event_engine.initialize()

        def fan_out(event: Event) -> None:
            for projection in self._projections:
                if projection.handles(event.type):
                    try:
                        projection.apply(event)
                    except Exception:
                        continue

        subscription = event_engine.subscribe("*", fan_out)
        with self._lock:
            self._subscriptions.append((event_engine, subscription))

    def rebuild_all(self) -> dict[str, int]:
        """Rebuild every registered projection."""
        counts: dict[str, int] = {}
        for projection in self._projections:
            counts[projection.name] = projection.rebuild()
        return counts

    def shutdown(self) -> None:
        with self._lock:
            for _, subscription in self._subscriptions:
                subscription.unsubscribe()
            self._subscriptions.clear()