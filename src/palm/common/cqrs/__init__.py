"""
CQRS primitives — commands, queries, and event-driven projections.

**Extend Palm CQRS**

1. Add a command or query dataclass under :mod:`palm.common.cqrs.command` or
   :mod:`palm.common.cqrs.query`.
2. Implement a projection in :mod:`palm.common.cqrs.projections` (optional for
   queries that read authoritative stores directly).
3. Register handlers in :mod:`palm.app.host.cqrs_wiring` and projections on the
   host :class:`~palm.app.host.ApplicationHost` during ``_wire_cqrs``.
4. Projections receive events automatically once registered and attached.
"""

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.command import Command, CommandHandler
from palm.common.cqrs.projection import Projection, ProjectionManager
from palm.common.cqrs.query import Query, QueryHandler

__all__ = [
    "Command",
    "CommandBus",
    "CommandHandler",
    "Projection",
    "ProjectionManager",
    "Query",
    "QueryBus",
    "QueryHandler",
]
