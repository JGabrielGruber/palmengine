"""
Event engine — observability and pub/sub.

Pure core module: no imports from outside ``palm.core``.
"""

from palm.core.event.engine import Event, EventEngine

__all__ = ["Event", "EventEngine"]
