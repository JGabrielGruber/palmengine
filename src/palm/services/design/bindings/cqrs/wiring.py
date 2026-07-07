"""Wire design service CQRS transport onto host buses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.services.design.bindings.cqrs.handlers import DesignCommandHandler, DesignQueryHandler
from palm.services.design.bindings.cqrs.registry import DESIGN_COMMAND_TYPES, DESIGN_QUERY_TYPES

if TYPE_CHECKING:
    from palm.services.design.service import DesignService


def wire_design_service_cqrs(
    command_bus: CommandBus,
    query_bus: QueryBus,
    design: DesignService,
) -> None:
    """Register design command/query handlers (transport only; rules live in DesignService)."""
    command_handler = DesignCommandHandler(design)
    query_handler = DesignQueryHandler(design)
    for command_type in DESIGN_COMMAND_TYPES:
        command_bus.register(command_type, command_handler)
    for query_type in DESIGN_QUERY_TYPES:
        query_bus.register(query_type, query_handler)


__all__ = ["wire_design_service_cqrs"]