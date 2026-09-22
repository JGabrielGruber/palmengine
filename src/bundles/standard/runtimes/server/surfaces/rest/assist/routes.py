"""Assist REST routes — command-path projection of assist dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bundles.standard.runtimes.server.surfaces.rest.assist import handlers
from bundles.standard.runtimes.server.surfaces.rest.bindings import bind_handler
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
        "get_instance",
        "GET",
        f"{API_PREFIX}/assist/instance/{{instance_id}}",
        "get_instance",
    ),
    RouteEntry(
        "instance_input",
        "POST",
        f"{API_PREFIX}/assist/instance/{{instance_id}}/input",
        "instance_input",
        auth_required=True,
    ),
    RouteEntry(
        "instance_backtrack",
        "POST",
        f"{API_PREFIX}/assist/instance/{{instance_id}}/backtrack",
        "instance_backtrack",
        auth_required=True,
    ),
    RouteEntry(
        "instance_resume",
        "POST",
        f"{API_PREFIX}/assist/instance/{{instance_id}}/resume",
        "instance_resume",
        auth_required=True,
    ),
    RouteEntry(
        "instance_cancel",
        "POST",
        f"{API_PREFIX}/assist/instance/{{instance_id}}/cancel",
        "instance_cancel",
        auth_required=True,
    ),
    RouteEntry(
        "instance_handoff",
        "POST",
        f"{API_PREFIX}/assist/instance/{{instance_id}}/handoff",
        "instance_handoff",
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
    "get_instance": handlers.get_instance,
    "instance_input": handlers.instance_input,
    "instance_backtrack": handlers.instance_backtrack,
    "instance_resume": handlers.instance_resume,
    "instance_cancel": handlers.instance_cancel,
    "instance_handoff": handlers.instance_handoff,
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