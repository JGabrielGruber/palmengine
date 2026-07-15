"""Flow execution REST routes — command-path projection of flows dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.bindings import bind_handler
from palm.runtimes.server.surfaces.rest.execution.flows import handlers
from palm.runtimes.server.surfaces.rest.prefix import API_PREFIX

if TYPE_CHECKING:
    from palm.common.runtimes.server.registry import RouteRegistry
    from palm.runtimes.server.context import ServerContext


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
        "get_session",
        "GET",
        f"{API_PREFIX}/flows/{{flow_id}}/session/{{session_id}}",
        "get_session",
    ),
    RouteEntry(
        "session_input",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/session/{{session_id}}/input",
        "session_input",
        auth_required=True,
    ),
    RouteEntry(
        "session_backtrack",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/session/{{session_id}}/backtrack",
        "session_backtrack",
        auth_required=True,
    ),
    RouteEntry(
        "session_resume",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/session/{{session_id}}/resume",
        "session_resume",
        auth_required=True,
    ),
    RouteEntry(
        "session_resume_child_wait",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/session/{{session_id}}/resume-child-wait",
        "session_resume_child_wait",
        auth_required=True,
    ),
    RouteEntry(
        "session_cancel",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/session/{{session_id}}/cancel",
        "session_cancel",
        auth_required=True,
    ),
)

_HANDLERS = {
    "list_flows": handlers.list_flows,
    "describe_flow": handlers.describe_flow,
    "create_session": handlers.create_session,
    "get_session": handlers.get_session,
    "session_input": handlers.session_input,
    "session_backtrack": handlers.session_backtrack,
    "session_resume": handlers.session_resume,
    "session_resume_child_wait": handlers.session_resume_child_wait,
    "session_cancel": handlers.session_cancel,
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