"""Mount per-service REST routes under ``/v1/api``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.definitions.routes import register_definitions_routes
from palm.runtimes.server.surfaces.rest.execution.flows.routes import register_flow_routes
from palm.runtimes.server.surfaces.rest.execution.providers.routes import register_provider_routes
from palm.runtimes.server.surfaces.rest.system.routes import register_system_routes

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


def register_service_routes(
    registry: RouteRegistry,
    ctx: ServerContext,
    *,
    surface: str,
) -> None:
    """Register definitions, flows, and system routes from runtime-owned tables."""
    register_definitions_routes(registry, ctx, surface=surface)
    register_flow_routes(registry, ctx, surface=surface)
    register_provider_routes(registry, ctx, surface=surface)
    register_system_routes(registry, ctx, surface=surface)


__all__ = ["register_service_routes"]