"""
Event subscription handles — unsubscribe without reaching into engine internals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.core.event.engine import EventEngine


@dataclass(frozen=True)
class Subscription:
    """Opaque handle returned by :meth:`~palm.core.event.EventEngine.subscribe`."""

    event_type: str
    subscription_id: int
    engine: EventEngine

    def unsubscribe(self) -> None:
        """Remove this handler from the event bus."""
        self.engine.unsubscribe(self)