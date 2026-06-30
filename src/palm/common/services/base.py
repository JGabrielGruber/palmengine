"""Base service — validated CQRS dispatch."""

from __future__ import annotations

from typing import Any

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.command import Command
from palm.common.cqrs.query import Query
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.common.services.errors import ServiceValidationError


class BaseService:
    """Shared CQRS access with schema validation before bus dispatch."""

    def __init__(
        self,
        *,
        commands: CommandBus,
        queries: QueryBus,
        schemas: CqrsSchemaRegistry,
    ) -> None:
        self._commands = commands
        self._queries = queries
        self._schemas = schemas

    @property
    def schemas(self) -> CqrsSchemaRegistry:
        return self._schemas

    def dispatch(self, command: Command) -> Any:
        result = self._schemas.validate(command)
        if not result.ok:
            raise ServiceValidationError(result, type(command))
        return self._commands.dispatch(command)

    def ask(self, query: Query) -> Any:
        result = self._schemas.validate(query)
        if not result.ok:
            raise ServiceValidationError(result, type(query))
        return self._queries.ask(query)


__all__ = ["BaseService"]
