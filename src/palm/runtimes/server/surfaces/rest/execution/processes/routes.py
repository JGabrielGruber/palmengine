"""Process execution REST routes under ``/v1/api/processes``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.bindings import bind_handler
from palm.runtimes.server.surfaces.rest.execution.processes import handlers
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
        "prepare_process",
        "POST",
        f"{API_PREFIX}/processes/{{process_id}}/prepare",
        "prepare_process",
        auth_required=True,
    ),
    RouteEntry(
        "submit_process",
        "POST",
        f"{API_PREFIX}/processes/submit",
        "submit_process",
        auth_required=True,
    ),
    RouteEntry(
        "run_process",
        "POST",
        f"{API_PREFIX}/processes/{{process_id}}/run",
        "run_process",
        auth_required=True,
    ),
)

_HANDLERS = {
    "prepare_process": handlers.prepare_process,
    "submit_process": handlers.submit_process,
    "run_process": handlers.run_process,
}


def register_process_routes(
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


__all__ = ["ROUTES", "RouteEntry", "register_process_routes"]