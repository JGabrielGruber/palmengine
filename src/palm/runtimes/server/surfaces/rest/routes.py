"""
REST route registration — binds :mod:`route_table` metadata to handlers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import RouteHandler
from palm.runtimes.server.surfaces.rest.handlers import meta
from palm.runtimes.server.surfaces.rest.service_routes import register_service_routes
from palm.runtimes.server.surfaces.rest.openapi_registry import meta_routes
from palm.runtimes.server.surfaces.rest.route_table import RouteDefinition, RouteId

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


def register_routes(
    registry: RouteRegistry,
    ctx: ServerContext,
    *,
    surface: str,
    surface_names: list[str],
) -> None:
    """Mount all REST routes on the shared registry."""
    for route in meta_routes():
        registry.register(
            method=route.method,
            path=route.path,
            handler=_resolve_handler(route, ctx, surface_names),
            surface=surface,
            auth_required=route.auth_required,
        )
    register_service_routes(registry, ctx, surface=surface)


def _resolve_handler(
    route: RouteDefinition,
    ctx: ServerContext,
    surface_names: list[str],
) -> RouteHandler:
    builders: dict[RouteId, RouteHandler] = {
        "health": lambda req: meta.health(ctx, surface_names),
        "openapi": lambda req: meta.openapi(ctx, req),
        "docs": lambda req: meta.docs(ctx, req),
    }
    return builders[route.route_id]