"""Wire definitions service CQRS transport onto buses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.services.definitions.bindings.cqrs.handlers import (
    DefinitionsCommandHandler,
    DefinitionsQueryHandler,
)
from palm.services.definitions.bindings.cqrs.registry import (
    DEFINITIONS_COMMAND_TYPES,
    DEFINITIONS_QUERY_TYPES,
)

if TYPE_CHECKING:
    from palm.common.managers.instance_manager import InstanceManager
    from palm.common.persistence.definition_repository import DefinitionRepository


@dataclass(frozen=True)
class DefinitionsWireContext:
    """Bootstrap context for definitions CQRS wiring."""

    repository: DefinitionRepository
    instance_manager: InstanceManager


def wire_definitions_service_cqrs(
    command_bus: CommandBus,
    query_bus: QueryBus,
    context: DefinitionsWireContext | Any,
) -> None:
    """Register definitions command/query handlers (overwrites generic bus handlers)."""
    if not isinstance(context, DefinitionsWireContext):
        context = DefinitionsWireContext(
            repository=context.repository,
            instance_manager=context.instance_manager,
        )
    commands = DefinitionsCommandHandler(
        repository=context.repository,
        instance_manager=context.instance_manager,
    )
    queries = DefinitionsQueryHandler(
        repository=context.repository,
        instance_manager=context.instance_manager,
    )
    for command_type in DEFINITIONS_COMMAND_TYPES:
        command_bus.register(command_type, commands)
    for query_type in DEFINITIONS_QUERY_TYPES:
        query_bus.register(query_type, queries)


__all__ = ["DefinitionsWireContext", "wire_definitions_service_cqrs"]