"""System service REST routes under ``/v1/api/system``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.bindings import bind_handler
from palm.runtimes.server.surfaces.rest.prefix import API_PREFIX
from palm.runtimes.server.surfaces.rest.system import handlers

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
    RouteEntry("doctor", "GET", f"{API_PREFIX}/system/doctor", "doctor"),
    RouteEntry("list_jobs", "GET", f"{API_PREFIX}/system/jobs", "list_jobs"),
    RouteEntry("get_job", "GET", f"{API_PREFIX}/system/jobs/{{job_id}}", "get_job"),
    RouteEntry(
        "inspect_job",
        "GET",
        f"{API_PREFIX}/system/jobs/{{job_id}}/context",
        "inspect_job",
    ),
    RouteEntry(
        "cancel_job",
        "POST",
        f"{API_PREFIX}/system/jobs/{{job_id}}/cancel",
        "cancel_job",
        auth_required=True,
    ),
    RouteEntry("list_instances", "GET", f"{API_PREFIX}/system/instances", "list_instances"),
    RouteEntry(
        "inspect_instance",
        "GET",
        f"{API_PREFIX}/system/instances/{{instance_id}}",
        "inspect_instance",
    ),
    RouteEntry(
        "instance_tree",
        "GET",
        f"{API_PREFIX}/system/instances/{{instance_id}}/tree",
        "instance_tree",
    ),
    RouteEntry(
        "list_snapshots",
        "GET",
        f"{API_PREFIX}/system/instances/{{instance_id}}/snapshots",
        "list_snapshots",
    ),
    RouteEntry(
        "get_snapshot",
        "GET",
        f"{API_PREFIX}/system/instances/{{instance_id}}/snapshots/{{snapshot_id}}",
        "get_snapshot",
    ),
    RouteEntry(
        "resume_instance",
        "POST",
        f"{API_PREFIX}/system/instances/{{instance_id}}/resume",
        "resume_instance",
        auth_required=True,
    ),
)

_HANDLERS = {
    "doctor": handlers.doctor,
    "list_jobs": handlers.list_jobs,
    "get_job": handlers.get_job,
    "inspect_job": handlers.inspect_job,
    "cancel_job": handlers.cancel_job,
    "list_instances": handlers.list_instances,
    "inspect_instance": handlers.inspect_instance,
    "instance_tree": handlers.instance_tree,
    "list_snapshots": handlers.list_snapshots,
    "get_snapshot": handlers.get_snapshot,
    "resume_instance": handlers.resume_instance,
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