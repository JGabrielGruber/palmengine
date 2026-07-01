"""Assist REST routes — command-path projection of assist dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.assist import handlers
from palm.runtimes.server.surfaces.rest.bindings import bind_handler
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
    RouteEntry("list_scenarios", "GET", f"{API_PREFIX}/assist/scenarios", "list_scenarios"),
    RouteEntry(
        "describe_scenario",
        "GET",
        f"{API_PREFIX}/assist/scenarios/{{scenario_id}}",
        "describe_scenario",
    ),
    RouteEntry(
        "start_scenario",
        "POST",
        f"{API_PREFIX}/assist/scenarios/{{scenario_id}}/start",
        "start_scenario",
        auth_required=True,
    ),
    RouteEntry(
        "get_session",
        "GET",
        f"{API_PREFIX}/assist/session/{{session_id}}",
        "get_session",
    ),
    RouteEntry(
        "session_input",
        "POST",
        f"{API_PREFIX}/assist/session/{{session_id}}/input",
        "session_input",
        auth_required=True,
    ),
    RouteEntry(
        "session_backtrack",
        "POST",
        f"{API_PREFIX}/assist/session/{{session_id}}/backtrack",
        "session_backtrack",
        auth_required=True,
    ),
    RouteEntry(
        "session_resume",
        "POST",
        f"{API_PREFIX}/assist/session/{{session_id}}/resume",
        "session_resume",
        auth_required=True,
    ),
    RouteEntry(
        "session_cancel",
        "POST",
        f"{API_PREFIX}/assist/session/{{session_id}}/cancel",
        "session_cancel",
        auth_required=True,
    ),
    RouteEntry(
        "session_handoff",
        "POST",
        f"{API_PREFIX}/assist/session/{{session_id}}/handoff",
        "session_handoff",
    ),
    RouteEntry("doctor", "GET", f"{API_PREFIX}/assist/doctor", "doctor"),
    RouteEntry(
        "catalog_flows",
        "GET",
        f"{API_PREFIX}/assist/catalog/flows",
        "catalog_flows",
    ),
)

_HANDLERS = {
    "list_scenarios": handlers.list_scenarios,
    "describe_scenario": handlers.describe_scenario,
    "start_scenario": handlers.start_scenario,
    "get_session": handlers.get_session,
    "session_input": handlers.session_input,
    "session_backtrack": handlers.session_backtrack,
    "session_resume": handlers.session_resume,
    "session_cancel": handlers.session_cancel,
    "session_handoff": handlers.session_handoff,
    "doctor": handlers.doctor,
    "catalog_flows": handlers.catalog_flows,
}


def register_assist_routes(
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


__all__ = ["ROUTES", "RouteEntry", "register_assist_routes"]