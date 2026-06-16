"""
Command and query buses — explicit dispatch registries.
"""

from __future__ import annotations

import threading
from typing import Any

from palm.common.cqrs.command import Command, CommandHandler
from palm.common.cqrs.query import Query, QueryHandler


class CommandBus:
    """Routes commands to registered handlers by type."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handlers: dict[type[Command], CommandHandler] = {}

    def register(self, command_type: type[Command], handler: CommandHandler) -> None:
        with self._lock:
            self._handlers[command_type] = handler

    def dispatch(self, command: Command) -> Any:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise TypeError(f"No handler registered for {type(command).__name__}")
        return handler.handle(command)


class QueryBus:
    """Routes queries to registered handlers by type."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handlers: dict[type[Query], QueryHandler] = {}

    def register(self, query_type: type[Query], handler: QueryHandler) -> None:
        with self._lock:
            self._handlers[query_type] = handler

    def ask(self, query: Query) -> Any:
        handler = self._handlers.get(type(query))
        if handler is None:
            raise TypeError(f"No handler registered for {type(query).__name__}")
        return handler.ask(query)