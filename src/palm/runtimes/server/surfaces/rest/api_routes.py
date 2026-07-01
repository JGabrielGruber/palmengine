"""
Service-domain REST routes under ``/v1/api``.

Route tables live in the runtime layer until Phase 2 command-path router lands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.runtimes.server.surfaces.rest.definitions import handlers as definitions_handlers
from palm.runtimes.server.surfaces.rest.execution.flows import handlers as flow_handlers
from palm.runtimes.server.surfaces.rest.prefix import API_PREFIX
from palm.runtimes.server.surfaces.rest.system import handlers as system_handlers

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.protocol import RouteHandler
    from palm.common.runtimes.server.registry import RouteRegistry


@dataclass(frozen=True)
class RestRouteEntry:
    route_id: str
    method: str
    path: str
    handler_name: str
    summary: str = ""
    auth_required: bool = False


_DEFINITIONS_ROUTES: tuple[RestRouteEntry, ...] = (
    RestRouteEntry("list_flows", "GET", f"{API_PREFIX}/definitions/flows", "list_flows"),
    RestRouteEntry("get_flow", "GET", f"{API_PREFIX}/definitions/flows/{{flow_id}}", "get_flow"),
    RestRouteEntry(
        "validate_flow",
        "POST",
        f"{API_PREFIX}/definitions/flows/validate",
        "validate_flow",
        auth_required=True,
    ),
    RestRouteEntry("list_processes", "GET", f"{API_PREFIX}/definitions/processes", "list_processes"),
    RestRouteEntry(
        "get_process",
        "GET",
        f"{API_PREFIX}/definitions/processes/{{process_id}}",
        "get_process",
    ),
    RestRouteEntry("list_resources", "GET", f"{API_PREFIX}/definitions/resources", "list_resources"),
    RestRouteEntry(
        "get_resource",
        "GET",
        f"{API_PREFIX}/definitions/resources/{{resource_ref}}",
        "get_resource",
    ),
)

_SYSTEM_ROUTES: tuple[RestRouteEntry, ...] = (
    RestRouteEntry("doctor", "GET", f"{API_PREFIX}/system/doctor", "doctor"),
    RestRouteEntry("list_jobs", "GET", f"{API_PREFIX}/system/jobs", "list_jobs"),
    RestRouteEntry("get_job", "GET", f"{API_PREFIX}/system/jobs/{{job_id}}", "get_job"),
)

_FLOW_ROUTES: tuple[RestRouteEntry, ...] = (
    RestRouteEntry(
        "create_flow_instance",
        "POST",
        f"{API_PREFIX}/flows/{{flow_id}}/instances",
        "create_instance",
        auth_required=True,
    ),
    RestRouteEntry(
        "get_flow_instance",
        "GET",
        f"{API_PREFIX}/flows/instances/{{instance_id}}",
        "get_instance",
    ),
    RestRouteEntry(
        "flow_instance_input",
        "POST",
        f"{API_PREFIX}/flows/instances/{{instance_id}}/input",
        "provide_input",
        auth_required=True,
    ),
    RestRouteEntry(
        "flow_instance_backtrack",
        "POST",
        f"{API_PREFIX}/flows/instances/{{instance_id}}/backtrack",
        "backtrack",
        auth_required=True,
    ),
    RestRouteEntry(
        "flow_instance_resume_child_wait",
        "POST",
        f"{API_PREFIX}/flows/instances/{{instance_id}}/resume-child-wait",
        "resume_child_wait",
        auth_required=True,
    ),
)


def register_api_routes(
    registry: RouteRegistry,
    ctx: ServerContext,
    *,
    surface: str,
) -> None:
    """Mount ``/v1/api`` routes from runtime-owned route tables."""
    for entry, handler in _handler_map(ctx):
        registry.register(
            method=entry.method,
            path=entry.path,
            handler=handler,
            surface=surface,
            auth_required=entry.auth_required,
        )


def _handler_map(ctx: ServerContext) -> list[tuple[RestRouteEntry, RouteHandler]]:
    bindings: dict[str, dict[str, Any]] = {
        "definitions": {
            "list_flows": definitions_handlers.list_flows,
            "get_flow": definitions_handlers.get_flow,
            "validate_flow": definitions_handlers.validate_flow,
            "list_processes": definitions_handlers.list_processes,
            "get_process": definitions_handlers.get_process,
            "list_resources": definitions_handlers.list_resources,
            "get_resource": definitions_handlers.get_resource,
        },
        "system": {
            "doctor": system_handlers.doctor,
            "list_jobs": system_handlers.list_jobs,
            "get_job": system_handlers.get_job,
        },
        "flows": {
            "create_instance": flow_handlers.create_instance,
            "get_instance": flow_handlers.get_instance,
            "provide_input": flow_handlers.provide_input,
            "backtrack": flow_handlers.backtrack,
            "resume_child_wait": flow_handlers.resume_child_wait,
        },
    }

    pairs: list[tuple[RestRouteEntry, RouteHandler]] = []
    for entry in _DEFINITIONS_ROUTES:
        fn = bindings["definitions"][entry.handler_name]
        pairs.append((entry, _bind(ctx, fn)))
    for entry in _SYSTEM_ROUTES:
        fn = bindings["system"][entry.handler_name]
        pairs.append((entry, _bind(ctx, fn)))
    for entry in _FLOW_ROUTES:
        fn = bindings["flows"][entry.handler_name]
        pairs.append((entry, _bind(ctx, fn)))
    return pairs


def _bind(ctx: ServerContext, fn: Any) -> RouteHandler:
    def _handler(request: Any, **params: str) -> Any:
        return fn(ctx, request, **params)

    return _handler