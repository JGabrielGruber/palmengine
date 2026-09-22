"""Workload execution REST routes under ``/v1/api/workloads``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bundles.standard.runtimes.server.surfaces.rest.bindings import bind_handler
from bundles.standard.runtimes.server.surfaces.rest.execution.workloads import handlers
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
    RouteEntry(
        "start_workload",
        "POST",
        f"{API_PREFIX}/workloads",
        "start_workload",
        auth_required=True,
    ),
    RouteEntry(
        "list_workloads",
        "GET",
        f"{API_PREFIX}/workloads",
        "list_workloads",
        auth_required=True,
    ),
    RouteEntry(
        "list_workload_runtimes",
        "GET",
        f"{API_PREFIX}/workloads/runtimes",
        "list_workload_runtimes",
        auth_required=True,
    ),
    RouteEntry(
        "list_workload_hosts",
        "GET",
        f"{API_PREFIX}/workloads/hosts",
        "list_workload_hosts",
        auth_required=True,
    ),
    RouteEntry(
        "workload_doctor",
        "GET",
        f"{API_PREFIX}/workloads/doctor",
        "workload_doctor",
        auth_required=True,
    ),
    RouteEntry(
        "get_workload",
        "GET",
        f"{API_PREFIX}/workloads/{{workload_id}}",
        "get_workload",
        auth_required=True,
    ),
    RouteEntry(
        "stop_workload",
        "POST",
        f"{API_PREFIX}/workloads/{{workload_id}}/stop",
        "stop_workload",
        auth_required=True,
    ),
    RouteEntry(
        "exec_workload",
        "POST",
        f"{API_PREFIX}/workloads/{{workload_id}}/exec",
        "exec_workload",
        auth_required=True,
    ),
)

_HANDLERS = {
    "start_workload": handlers.start_workload,
    "list_workloads": handlers.list_workloads,
    "list_workload_runtimes": handlers.list_workload_runtimes,
    "list_workload_hosts": handlers.list_workload_hosts,
    "workload_doctor": handlers.workload_doctor,
    "get_workload": handlers.get_workload,
    "stop_workload": handlers.stop_workload,
    "exec_workload": handlers.exec_workload,
}


def register_workload_routes(
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


__all__ = ["ROUTES", "RouteEntry", "register_workload_routes"]
