"""
REST route metadata — declarative table without handler imports.

Shared by route registration, OpenAPI generation, and HTML docs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RouteId = Literal[
    "health",
    "openapi",
    "docs",
    "list_jobs",
    "get_job",
    "get_job_context",
    "submit_job",
    "provide_input",
    "prepare_plans",
    "submit_plans",
    "list_instances",
    "get_instance",
    "resume_instance",
    "list_snapshots",
    "get_snapshot",
    "list_flows",
    "get_flow",
    "list_processes",
    "get_process",
]


@dataclass(frozen=True)
class RouteDefinition:
    """Declarative route with OpenAPI-oriented metadata."""

    route_id: RouteId
    method: str
    path: str
    group: str
    summary: str
    description: str = ""
    auth_required: bool = False
    request_schema: str | None = None
    query_schema: str | None = None
    response_status: int = 200


def rest_routes() -> tuple[RouteDefinition, ...]:
    """Return the full REST route table grouped by resource."""
    return (
        RouteDefinition(
            route_id="health",
            method="GET",
            path="/health",
            group="Meta",
            summary="Health check",
            description="Runtime status, mounted surfaces, and documentation links.",
        ),
        RouteDefinition(
            route_id="openapi",
            method="GET",
            path="/v1/openapi.json",
            group="Meta",
            summary="OpenAPI document",
            description="Machine-readable API specification (OpenAPI 3.0).",
        ),
        RouteDefinition(
            route_id="docs",
            method="GET",
            path="/v1/docs",
            group="Meta",
            summary="API documentation",
            description="Human-readable HTML overview with endpoint groups.",
        ),
        RouteDefinition(
            route_id="list_jobs",
            method="GET",
            path="/v1/jobs",
            group="Jobs",
            summary="List jobs",
            description="Paginated orchestration job status board.",
            query_schema="ListJobsQuery",
        ),
        RouteDefinition(
            route_id="get_job",
            method="GET",
            path="/v1/jobs/{job_id}",
            group="Jobs",
            summary="Get job",
            description="Fetch a single job by id.",
        ),
        RouteDefinition(
            route_id="get_job_context",
            method="GET",
            path="/v1/jobs/{job_id}/context",
            group="Jobs",
            summary="Get job context",
            description=(
                "Rich job view with pattern state, wizard progress, blackboard snapshot, "
                "recent events, next actions, and related instance link."
            ),
        ),
        RouteDefinition(
            route_id="submit_job",
            method="POST",
            path="/v1/jobs",
            group="Jobs",
            summary="Submit job",
            description="Submit a flow, wizard, or named flow as an orchestration job.",
            auth_required=True,
            request_schema="SubmitJobBody",
            response_status=202,
        ),
        RouteDefinition(
            route_id="provide_input",
            method="POST",
            path="/v1/jobs/{job_id}/input",
            group="Jobs",
            summary="Provide input",
            description="Deliver interactive input to a waiting job.",
            auth_required=True,
            request_schema="ProvideInputBody",
        ),
        RouteDefinition(
            route_id="prepare_plans",
            method="POST",
            path="/v1/plans/prepare",
            group="Plans",
            summary="Prepare plans",
            description="Stage execution plans for deferred submission.",
            auth_required=True,
            request_schema="PreparePlansBody",
            response_status=201,
        ),
        RouteDefinition(
            route_id="submit_plans",
            method="POST",
            path="/v1/plans/submit",
            group="Plans",
            summary="Submit plans",
            description="Consume staged plan ids and submit orchestration jobs.",
            auth_required=True,
            request_schema="SubmitPlansBody",
            response_status=202,
        ),
        RouteDefinition(
            route_id="list_instances",
            method="GET",
            path="/v1/instances",
            group="Instances",
            summary="List instances",
            description="Paginated durable process instance index.",
            query_schema="ListInstancesQuery",
        ),
        RouteDefinition(
            route_id="get_instance",
            method="GET",
            path="/v1/instances/{instance_id}",
            group="Instances",
            summary="Get instance",
            description="Fetch a single process instance by id.",
        ),
        RouteDefinition(
            route_id="resume_instance",
            method="POST",
            path="/v1/instances/{instance_id}/resume",
            group="Instances",
            summary="Resume instance",
            description="Resume a persisted process instance.",
            auth_required=True,
            response_status=202,
        ),
        RouteDefinition(
            route_id="list_snapshots",
            method="GET",
            path="/v1/instances/{instance_id}/snapshots",
            group="Snapshots",
            summary="List snapshots",
            description="Paginated state snapshots for a durable process instance.",
            query_schema="ListSnapshotsQuery",
        ),
        RouteDefinition(
            route_id="get_snapshot",
            method="GET",
            path="/v1/instances/{instance_id}/snapshots/{snapshot_id}",
            group="Snapshots",
            summary="Get snapshot",
            description="Fetch a single state snapshot by zero-based index or recorded_at timestamp.",
        ),
        RouteDefinition(
            route_id="list_flows",
            method="GET",
            path="/v1/flows",
            group="Catalog",
            summary="List flows",
            description="Paginated registered flow definitions from the repository.",
            query_schema="ListFlowsQuery",
        ),
        RouteDefinition(
            route_id="get_flow",
            method="GET",
            path="/v1/flows/{flow_id}",
            group="Catalog",
            summary="Get flow",
            description="Fetch a full flow definition by id or name.",
        ),
        RouteDefinition(
            route_id="list_processes",
            method="GET",
            path="/v1/processes",
            group="Catalog",
            summary="List processes",
            description="Paginated registered process definitions from the repository.",
            query_schema="ListFlowsQuery",
        ),
        RouteDefinition(
            route_id="get_process",
            method="GET",
            path="/v1/processes/{process_id}",
            group="Catalog",
            summary="Get process",
            description="Fetch a full process definition by id or name.",
        ),
    )