"""Definitions service REST routes under ``/v1/api/definitions``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.bindings import bind_handler
from palm.runtimes.server.surfaces.rest.definitions import handlers
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
    RouteEntry("list_flows", "GET", f"{API_PREFIX}/definitions/flows", "list_flows"),
    RouteEntry("get_flow", "GET", f"{API_PREFIX}/definitions/flows/{{flow_id}}", "get_flow"),
    RouteEntry(
        "validate_flow",
        "POST",
        f"{API_PREFIX}/definitions/flows/validate",
        "validate_flow",
        auth_required=True,
    ),
    RouteEntry("list_processes", "GET", f"{API_PREFIX}/definitions/processes", "list_processes"),
    RouteEntry(
        "get_process",
        "GET",
        f"{API_PREFIX}/definitions/processes/{{process_id}}",
        "get_process",
    ),
    RouteEntry("list_resources", "GET", f"{API_PREFIX}/definitions/resources", "list_resources"),
    RouteEntry(
        "get_resource",
        "GET",
        f"{API_PREFIX}/definitions/resources/{{resource_ref}}",
        "get_resource",
    ),
)

_HANDLERS = {
    "list_flows": handlers.list_flows,
    "get_flow": handlers.get_flow,
    "validate_flow": handlers.validate_flow,
    "list_processes": handlers.list_processes,
    "get_process": handlers.get_process,
    "list_resources": handlers.list_resources,
    "get_resource": handlers.get_resource,
}


def register_definitions_routes(
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


__all__ = ["ROUTES", "RouteEntry", "register_definitions_routes"]