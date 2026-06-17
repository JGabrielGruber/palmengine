"""
Event engine — observability and pub/sub.

Pure core module: no imports from outside ``palm.core``.
"""

from palm.core.event.context import EventContext
from palm.core.event.engine import Event, EventEngine
from palm.core.event.errors import HandlerError, PublishResult
from palm.core.event.subscription import Subscription

__all__ = [
    "Event",
    "EventContext",
    "EventEngine",
    "HandlerError",
    "PublishResult",
    "Subscription",
]
