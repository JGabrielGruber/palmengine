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
    RouteEntry(
        "create_flow",
        "POST",
        f"{API_PREFIX}/definitions/flows",
        "create_flow",
        auth_required=True,
    ),
    RouteEntry(
        "analyze_flow_impact",
        "GET",
        f"{API_PREFIX}/definitions/flows/{{flow_id}}/impact",
        "analyze_flow_impact",
    ),
    RouteEntry(
        "migrate_instance",
        "POST",
        f"{API_PREFIX}/definitions/instances/{{instance_id}}/migrate",
        "migrate_instance",
        auth_required=True,
    ),
    RouteEntry("get_flow", "GET", f"{API_PREFIX}/definitions/flows/{{flow_id}}", "get_flow"),
    RouteEntry(
        "update_flow",
        "PUT",
        f"{API_PREFIX}/definitions/flows/{{flow_id}}",
        "update_flow",
        auth_required=True,
    ),
    RouteEntry(
        "delete_flow",
        "DELETE",
        f"{API_PREFIX}/definitions/flows/{{flow_id}}",
        "delete_flow",
        auth_required=True,
    ),
    RouteEntry(
        "validate_flow",
        "POST",
        f"{API_PREFIX}/definitions/flows/validate",
        "validate_flow",
        auth_required=True,
    ),
    RouteEntry("list_processes", "GET", f"{API_PREFIX}/definitions/processes", "list_processes"),
    RouteEntry(
        "create_process",
        "POST",
        f"{API_PREFIX}/definitions/processes",
        "create_process",
        auth_required=True,
    ),
    RouteEntry(
        "get_process",
        "GET",
        f"{API_PREFIX}/definitions/processes/{{process_id}}",
        "get_process",
    ),
    RouteEntry(
        "update_process",
        "PUT",
        f"{API_PREFIX}/definitions/processes/{{process_id}}",
        "update_process",
        auth_required=True,
    ),
    RouteEntry(
        "delete_process",
        "DELETE",
        f"{API_PREFIX}/definitions/processes/{{process_id}}",
        "delete_process",
        auth_required=True,
    ),
    RouteEntry("list_resources", "GET", f"{API_PREFIX}/definitions/resources", "list_resources"),
    RouteEntry(
        "create_resource",
        "POST",
        f"{API_PREFIX}/definitions/resources",
        "create_resource",
        auth_required=True,
    ),
    RouteEntry(
        "get_resource",
        "GET",
        f"{API_PREFIX}/definitions/resources/{{resource_ref}}",
        "get_resource",
    ),
    RouteEntry(
        "update_resource",
        "PUT",
        f"{API_PREFIX}/definitions/resources/{{resource_ref}}",
        "update_resource",
        auth_required=True,
    ),
    RouteEntry(
        "delete_resource",
        "DELETE",
        f"{API_PREFIX}/definitions/resources/{{resource_ref}}",
        "delete_resource",
        auth_required=True,
    ),
)

_HANDLERS = {
    "list_flows": handlers.list_flows,
    "create_flow": handlers.create_flow,
    "analyze_flow_impact": handlers.analyze_flow_impact,
    "migrate_instance": handlers.migrate_instance,
    "get_flow": handlers.get_flow,
    "update_flow": handlers.update_flow,
    "delete_flow": handlers.delete_flow,
    "validate_flow": handlers.validate_flow,
    "list_processes": handlers.list_processes,
    "create_process": handlers.create_process,
    "get_process": handlers.get_process,
    "update_process": handlers.update_process,
    "delete_process": handlers.delete_process,
    "list_resources": handlers.list_resources,
    "create_resource": handlers.create_resource,
    "get_resource": handlers.get_resource,
    "update_resource": handlers.update_resource,
    "delete_resource": handlers.delete_resource,
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