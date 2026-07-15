"""Provider execution REST routes under ``/v1/api/providers``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.bindings import bind_handler
from palm.runtimes.server.surfaces.rest.execution.providers import handlers
from palm.runtimes.server.surfaces.rest.prefix import API_PREFIX

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


@dataclass(frozen=True)
class RouteEntry:
    route_id: str
    method: str
    path: str
    handler_name: str
    auth_required: bool = False


ROUTES: tuple[RouteEntry, ...] = (
    RouteEntry(
        "invoke_provider",
        "POST",
        f"{API_PREFIX}/providers/{{provider}}/{{resource_ref}}/invoke",
        "invoke_provider",
        auth_required=True,
    ),
    RouteEntry(
        "invoke_resource",
        "POST",
        f"{API_PREFIX}/resources/{{resource_ref}}/invoke",
        "invoke_resource",
        auth_required=True,
    ),
)

_HANDLERS = {
    "invoke_provider": handlers.invoke_provider,
    "invoke_resource": handlers.invoke_resource,
}


def register_provider_routes(
    registry: RouteRegistry,
    ctx: ServerContext,
    *,
    surface: str,
) -> None:
    for entry in ROUTES:
        fn = _HANDLERS[entry.handler_name]
        registry.register(
            method=entry.method,
            path=entry.path,
            handler=bind_handler(ctx, fn),
            surface=surface,
            auth_required=entry.auth_required,
        )


__all__ = ["ROUTES", "RouteEntry", "register_provider_routes"]