"""Flow execution REST routes — command-path projection of flows dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bundles.standard.runtimes.server.surfaces.rest.bindings import bind_handler
from bundles.standard.runtimes.server.surfaces.rest.execution.flows import handlers
from bundles.standard.runtimes.server.surfaces.rest.prefix import API_PREFIX

if TYPE_CHECKING:
    from plugins.kits.server.registry import RouteRegistry
    from bundles.standard.runtimes.server.context import ServerContext


@dataclass(frozen=True)
class RouteEntry:
    route_id: str
    method: str
    path: str
    handler_name: str
    auth_required: bool = False


ROUTES: tuple[RouteEntry, ...] = (
    RouteEntry("list_flows", "GET", f"{API_PREFIX}/flows", "list_flows"),
    RouteEntry("describe_flow", "GET", f"{API_PREFIX}/flows/{{flow_id}}", "describe_flow"),
    RouteEntry(
        "create_session",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/create",
        "create_session",
        auth_required=True,
    ),
    RouteEntry(
        "get_instance",
        "GET",
        f"{API_PREFIX}/flows/{{flow_id}}/instance/{{instance_id}}",
        "get_instance",
    ),
    RouteEntry(
        "instance_input",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/instance/{{instance_id}}/input",
        "instance_input",
        auth_required=True,
    ),
    RouteEntry(
        "instance_backtrack",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/instance/{{instance_id}}/backtrack",
        "instance_backtrack",
        auth_required=True,
    ),
    RouteEntry(
        "instance_resume",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/instance/{{instance_id}}/resume",
        "instance_resume",
        auth_required=True,
    ),
    RouteEntry(
        "instance_cancel",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/instance/{{instance_id}}/cancel",
        "instance_cancel",
        auth_required=True,
    ),
)

_HANDLERS = {
    "list_flows": handlers.list_flows,
    "describe_flow": handlers.describe_flow,
    "create_session": handlers.create_session,
    "get_instance": handlers.get_instance,
    "instance_input": handlers.instance_input,
    "instance_backtrack": handlers.instance_backtrack,
    "instance_resume": handlers.instance_resume,
    "instance_cancel": handlers.instance_cancel,
}


def register_flow_routes(
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


__all__ = ["ROUTES", "RouteEntry", "register_flow_routes"]