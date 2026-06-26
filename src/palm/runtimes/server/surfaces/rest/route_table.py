"""
REST route metadata — declarative table without handler imports.

Shared by route registration, OpenAPI generation, and HTML docs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RouteId = Literal[
    "health",
    "doctor",
    "openapi",
    "docs",
    "list_jobs",
    "get_job",
    "get_job_context",
    "submit_job",
    "cancel_job",
    "provide_input",
    "submit_wizard",
    "get_wizard",
    "provide_wizard_input",
    "backtrack_wizard",
    "resume_child_wait",
    "resume_wizard_tick",
    "prepare_plans",
    "submit_plans",
    "list_instances",
    "get_instance",
    "get_instance_tree",
    "resume_instance",
    "list_snapshots",
    "get_snapshot",
    "validate_flow",
    "list_flows",
    "get_flow",
    "list_processes",
    "get_process",
    "list_resources",
    "get_resource",
    "invoke_resource",
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
            route_id="doctor",
            method="GET",
            path="/v1/doctor",
            group="Meta",
            summary="Engine doctor",
            description="Registry health, storage status, and job counts for operators.",
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
            route_id="cancel_job",
            method="POST",
            path="/v1/jobs/{job_id}/cancel",
            group="Jobs",
            summary="Cancel job",
            description="Cancel a non-terminal orchestration job.",
            auth_required=True,
        ),
        RouteDefinition(
            route_id="submit_wizard",
            method="POST",
            path="/v1/wizards",
            group="Wizards",
            summary="Submit wizard",
            description=(
                "Start an interactive wizard flow. Equivalent to submitting a flow with "
                "``pattern='wizard'``; returns the durable ``instance_id``."
            ),
            auth_required=True,
            request_schema="SubmitWizardBody",
            response_status=202,
        ),
        RouteDefinition(
            route_id="get_wizard",
            method="GET",
            path="/v1/wizards/{instance_id}",
            group="Wizards",
            summary="Get wizard",
            description=(
                "Rich wizard view: instance status, step progress, current prompt, "
                "answers, and suggested next actions."
            ),
        ),
        RouteDefinition(
            route_id="provide_wizard_input",
            method="POST",
            path="/v1/wizards/{instance_id}/input",
            group="Wizards",
            summary="Provide wizard input",
            description=(
                "Deliver interactive input to a waiting wizard step. "
                "Accepts scalars or structured values for collection steps."
            ),
            auth_required=True,
            request_schema="WizardInputBody",
        ),
        RouteDefinition(
            route_id="backtrack_wizard",
            method="POST",
            path="/v1/wizards/{instance_id}/backtrack",
            group="Wizards",
            summary="Backtrack wizard",
            description=(
                "Backtrack to a prior step. Omit ``to_step`` to return to the "
                "immediately preceding step."
            ),
            auth_required=True,
            request_schema="WizardBacktrackBody",
        ),
        RouteDefinition(
            route_id="resume_child_wait",
            method="POST",
            path="/v1/wizards/{instance_id}/resume-child-wait",
            group="Wizards",
            summary="Resume child wait",
            description=(
                "Re-check a nested child wizard and advance the parent resource step "
                "when the child reaches a terminal state."
            ),
            auth_required=True,
        ),
        RouteDefinition(
            route_id="resume_wizard_tick",
            method="POST",
            path="/v1/wizards/{instance_id}/resume-wizard-tick",
            group="Wizards",
            summary="Resume wizard tick",
            description=(
                "Re-drive a waiting wizard (for example auto-run a resource step)."
            ),
            auth_required=True,
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
            route_id="get_instance_tree",
            method="GET",
            path="/v1/instances/{instance_id}/tree",
            group="Instances",
            summary="Get instance invoke tree",
            description=(
                "Compositional invoke stack: root, ancestors, active child, and "
                "operator links for nested wizard flows."
            ),
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
            route_id="validate_flow",
            method="POST",
            path="/v1/flows/validate",
            group="Catalog",
            summary="Validate flow",
            description="Dry-run flow definition build without submitting a job.",
            auth_required=True,
            request_schema="ValidateFlowBody",
        ),
        RouteDefinition(
            route_id="list_flows",
            method="GET",
            path="/v1/flows",
            group="Catalog",
            description="Paginated registered flow definitions from the repository.",
            summary="List flows",
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
        RouteDefinition(
            route_id="list_resources",
            method="GET",
            path="/v1/resources",
            group="Resources",
            summary="List resources",
            description="Paginated resource definition catalog with provider and param metadata.",
            query_schema="ListFlowsQuery",
        ),
        RouteDefinition(
            route_id="get_resource",
            method="GET",
            path="/v1/resources/{resource_ref}",
            group="Resources",
            summary="Get resource",
            description="Describe a resource definition by name or id (params schema, provider, action).",
        ),
        RouteDefinition(
            route_id="invoke_resource",
            method="POST",
            path="/v1/resources/invoke",
            group="Resources",
            summary="Invoke resource",
            description="Invoke a registered resource definition via ResourceEngine.",
            auth_required=True,
            request_schema="InvokeResourceBody",
            response_status=200,
        ),
    )
