"""CQRS primitives — commands, queries, and event-driven projections."""

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