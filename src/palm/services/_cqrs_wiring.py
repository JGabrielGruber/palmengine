"""Wire all registered service-domain CQRS contributors onto buses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.service_contributors import wire_service_cqrs_contributors
from palm.services.definitions.bindings.cqrs.wiring import DefinitionsWireContext
from palm.services.design.bindings.cqrs.contributor import DesignWireContext

if TYPE_CHECKING:
    from palm.common.cqrs.bus import CommandBus, QueryBus
    from palm.common.managers.instance_manager import InstanceManager
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.services.design.service import DesignService


def wire_all_service_cqrs(
    command_bus: CommandBus,
    query_bus: QueryBus,
    *,
    repository: DefinitionRepository,
    instance_manager: InstanceManager,
    design: DesignService,
) -> None:
    """Register definitions and design service handlers (overwrites generic handlers)."""
    wire_service_cqrs_contributors(
        command_bus,
        query_bus,
        {
            "definitions": DefinitionsWireContext(
                repository=repository,
                instance_manager=instance_manager,
            ),
            "design": DesignWireContext(design=design),
        },
    )


def wire_all_service_cqrs_from_runtime(
    command_bus: Any,
    query_bus: Any,
    runtime: Any,
    *,
    design: DesignService,
) -> None:
    """Convenience wrapper for standalone :class:`ServerContext` bootstrap."""
    wire_all_service_cqrs(
        command_bus,
        query_bus,
        repository=runtime.repository,
        instance_manager=runtime.instance_manager,
        design=design,
    )


__all__ = ["wire_all_service_cqrs", "wire_all_service_cqrs_from_runtime"]