"""
REST route registration — binds :mod:`route_table` metadata to handlers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import RouteHandler
from palm.runtimes.server.surfaces.rest.handlers import (
    catalog,
    instances,
    jobs,
    meta,
    plans,
    resources,
    snapshots,
    wizard,
)
from palm.runtimes.server.surfaces.rest.api_routes import register_api_routes
from palm.runtimes.server.surfaces.rest.route_table import RouteDefinition, RouteId, rest_routes

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


def register_routes(
    registry: RouteRegistry,
    ctx: ServerContext,
    *,
    surface: str,
    surface_names: list[str],
) -> None:
    """Mount all REST routes on the shared registry."""
    for route in rest_routes():
        registry.register(
            method=route.method,
            path=route.path,
            handler=_resolve_handler(route, ctx, surface_names),
            surface=surface,
            auth_required=route.auth_required,
        )
    register_api_routes(registry, ctx, surface=surface)


def _resolve_handler(
    route: RouteDefinition,
    ctx: ServerContext,
    surface_names: list[str],
) -> RouteHandler:
    builders: dict[RouteId, RouteHandler] = {
        "health": lambda req: meta.health(ctx, surface_names),
        "doctor": lambda req: meta.doctor(ctx, req),
        "openapi": lambda req: meta.openapi(ctx, req),
        "docs": lambda req: meta.docs(ctx, req),
        "list_jobs": lambda req: jobs.list_jobs(ctx, req),
        "get_job": lambda req, job_id: jobs.get_job(ctx, req, job_id=job_id),
        "get_job_context": lambda req, job_id: jobs.get_job_context(ctx, req, job_id=job_id),
        "submit_job": lambda req: jobs.submit_job(ctx, req),
        "provide_input": lambda req, job_id: jobs.provide_input(ctx, req, job_id=job_id),
        "cancel_job": lambda req, job_id: jobs.cancel_job(ctx, req, job_id=job_id),
        "submit_wizard": lambda req: wizard.submit_wizard(ctx, req),
        "get_wizard": lambda req, instance_id: wizard.get_wizard(ctx, req, instance_id=instance_id),
        "provide_wizard_input": lambda req, instance_id: wizard.provide_wizard_input(
            ctx, req, instance_id=instance_id
        ),
        "backtrack_wizard": lambda req, instance_id: wizard.backtrack_wizard(
            ctx, req, instance_id=instance_id
        ),
        "resume_child_wait": lambda req, instance_id: wizard.resume_child_wait(
            ctx, req, instance_id=instance_id
        ),
        "resume_wizard_tick": lambda req, instance_id: wizard.resume_wizard_tick(
            ctx, req, instance_id=instance_id
        ),
        "prepare_plans": lambda req: plans.prepare_plans(ctx, req),
        "submit_plans": lambda req: plans.submit_plans(ctx, req),
        "list_instances": lambda req: instances.list_instances(ctx, req),
        "get_instance": lambda req, instance_id: instances.get_instance(
            ctx, req, instance_id=instance_id
        ),
        "get_instance_tree": lambda req, instance_id: instances.get_instance_tree(
            ctx, req, instance_id=instance_id
        ),
        "resume_instance": lambda req, instance_id: instances.resume_instance(
            ctx, req, instance_id=instance_id
        ),
        "list_snapshots": lambda req, instance_id: snapshots.list_snapshots(
            ctx, req, instance_id=instance_id
        ),
        "get_snapshot": lambda req, instance_id, snapshot_id: snapshots.get_snapshot(
            ctx, req, instance_id=instance_id, snapshot_id=snapshot_id
        ),
        "validate_flow": lambda req: catalog.validate_flow(ctx, req),
        "list_flows": lambda req: catalog.list_flows(ctx, req),
        "get_flow": lambda req, flow_id: catalog.get_flow(ctx, req, flow_id=flow_id),
        "list_processes": lambda req: catalog.list_processes(ctx, req),
        "get_process": lambda req, process_id: catalog.get_process(ctx, req, process_id=process_id),
        "list_resources": lambda req: resources.list_resources(ctx, req),
        "get_resource": lambda req, resource_ref: resources.get_resource(
            ctx, req, resource_ref=resource_ref
        ),
        "invoke_resource": lambda req: resources.invoke_resource(ctx, req),
    }
    return builders[route.route_id]
