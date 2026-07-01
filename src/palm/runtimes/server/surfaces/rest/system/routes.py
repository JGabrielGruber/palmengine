"""System service REST routes under ``/v1/api/system``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.bindings import bind_handler
from palm.runtimes.server.surfaces.rest.prefix import API_PREFIX
from palm.runtimes.server.surfaces.rest.system import handlers

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
    RouteEntry("doctor", "GET", f"{API_PREFIX}/system/doctor", "doctor"),
    RouteEntry("list_jobs", "GET", f"{API_PREFIX}/system/jobs", "list_jobs"),
    RouteEntry("get_job", "GET", f"{API_PREFIX}/system/jobs/{{job_id}}", "get_job"),
)

_HANDLERS = {
    "doctor": handlers.doctor,
    "list_jobs": handlers.list_jobs,
    "get_job": handlers.get_job,
}


def register_system_routes(
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


__all__ = ["ROUTES", "RouteEntry", "register_system_routes"]