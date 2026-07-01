"""Aggregate REST route metadata from per-service route registries."""

from __future__ import annotations

from dataclasses import dataclass

from palm.runtimes.server.surfaces.rest.assist import routes as assist_routes
from palm.runtimes.server.surfaces.rest.definitions import routes as definitions_routes
from palm.runtimes.server.surfaces.rest.execution.flows import routes as flows_routes
from palm.runtimes.server.surfaces.rest.execution.processes import routes as processes_routes
from palm.runtimes.server.surfaces.rest.execution.providers import routes as providers_routes
from palm.runtimes.server.surfaces.rest.route_table import RouteDefinition
from palm.runtimes.server.surfaces.rest.system import routes as system_routes
from palm.services.assist.registry import assist_commands
from palm.services.definitions.registry import catalog_verbs
from palm.services.execution.flows.registry import flow_commands
from palm.services.execution.processes.registry import process_commands
from palm.services.execution.providers.registry import invoke_verbs
from palm.services.system.registry import observe_verbs

_SERVICE_GROUPS = {
    "assist": "Assist",
    "definitions": "Definitions",
    "flows": "Flows",
    "processes": "Processes",
    "providers": "Providers",
    "system": "System",
}

_PROCESS_COMMAND_IDS = {
    "prepare_process": "prepare",
    "submit_process": "submit",
    "run_process": "run",
}

_FLOW_COMMAND_IDS = {
    "get_session": "session_context",
}

_ASSIST_COMMAND_IDS = {
    "get_session": "session_context",
    "start_scenario": "start_scenario",
    "session_handoff": "session_handoff",
}


@dataclass(frozen=True)
class _RouteDoc:
    group: str
    summary: str
    description: str = ""
    request_schema: str | None = None
    query_schema: str | None = None
    response_status: int = 200
    route_id: str | None = None


def _summary_index() -> dict[str, str]:
    summaries: dict[str, str] = {}
    for verb in observe_verbs():
        summaries[verb.verb_id] = verb.summary
    for verb in catalog_verbs():
        summaries[verb.verb_id] = verb.summary
    for command in flow_commands():
        summaries[command.command_id] = command.summary
    for command in assist_commands():
        summaries[command.command_id] = command.summary
    for command in process_commands():
        summaries[command.command_id] = command.summary
    for verb in invoke_verbs():
        summaries[verb.verb_id] = verb.summary
    return summaries


def _resolve_summary(route_id: str, summaries: dict[str, str]) -> str:
    if route_id in summaries:
        return summaries[route_id]
    if route_id in _PROCESS_COMMAND_IDS:
        return summaries.get(_PROCESS_COMMAND_IDS[route_id], route_id.replace("_", " ").title())
    if route_id in _FLOW_COMMAND_IDS:
        return summaries.get(_FLOW_COMMAND_IDS[route_id], route_id.replace("_", " ").title())
    if route_id in _ASSIST_COMMAND_IDS:
        return summaries.get(_ASSIST_COMMAND_IDS[route_id], route_id.replace("_", " ").title())
    return route_id.replace("_", " ").title()


_DESCRIPTIONS: dict[str, str] = {
    "doctor": "Engine health report with registry and storage diagnostics.",
    "list_jobs": "Paginated orchestration job status board.",
    "get_job": "Fetch a single job by id.",
    "inspect_job": (
        "Rich job view with pattern state, wizard progress, blackboard snapshot, "
        "recent events, next actions, and related instance link."
    ),
    "cancel_job": "Cancel a non-terminal orchestration job.",
    "list_instances": "Paginated durable process instance index.",
    "inspect_instance": "Pattern-aware inspect for a durable process instance.",
    "instance_tree": (
        "Compositional invoke stack: root, ancestors, active child, and "
        "operator links for nested wizard flows."
    ),
    "resume_instance": "Resume a persisted process instance.",
    "list_snapshots": "Paginated state snapshots for a durable process instance.",
    "get_snapshot": "Fetch a single state snapshot by zero-based index or recorded_at timestamp.",
    "list_flows": "List runnable flows exposed by the execution service.",
    "definitions_list_flows": "List flow definitions in the catalog.",
    "describe_flow": "Describe one runnable flow.",
    "create_session": "Start an interactive flow session (wizard REPL entry).",
    "get_session": "Inspect an active flow session context.",
    "session_input": "Deliver interactive input to a waiting session.",
    "session_backtrack": "Backtrack to a prior wizard step.",
    "session_resume": "Resume a waiting interactive flow session.",
    "session_resume_child_wait": "Resume a parent session after a nested child wait.",
    "session_cancel": "Cancel the session job.",
    "prepare_process": "Stage execution plans for deferred submission.",
    "submit_process": "Consume staged plan ids and submit orchestration jobs.",
    "run_process": "Prepare and submit a process in one call.",
    "invoke_provider": "Invoke a provider resource action.",
    "list_scenarios": "List registered assist scenarios for operator entry.",
    "describe_scenario": "Describe one assist scenario and its catalog flow.",
    "start_scenario": "Start an assist scenario session (wizard REPL entry).",
    "session_handoff": "Emit typed handoff payload for business flow entry.",
}

_REQUEST_SCHEMAS: dict[str, str] = {
    "create_session": "SubmitWizardBody",
    "session_input": "WizardInputBody",
    "start_scenario": "SubmitWizardBody",
    "session_backtrack": "WizardBacktrackBody",
    "prepare_process": "PreparePlansBody",
    "submit_process": "SubmitPlansBody",
    "run_process": "PreparePlansBody",
    "validate_flow": "ValidateFlowBody",
}

_QUERY_SCHEMAS: dict[str, str] = {
    "list_jobs": "ListJobsQuery",
    "list_instances": "ListInstancesQuery",
    "list_snapshots": "ListSnapshotsQuery",
    "definitions_list_flows": "ListFlowsQuery",
    "list_flows": "ListFlowsQuery",
}

_RESPONSE_STATUS: dict[str, int] = {
    "create_session": 202,
    "start_scenario": 202,
    "prepare_process": 201,
    "submit_process": 202,
    "run_process": 202,
    "resume_instance": 202,
    "create_flow": 201,
    "create_process": 201,
    "create_resource": 201,
}


def _doc_route_id(source: str, route_id: str) -> str:
    if source == "definitions" and route_id == "list_flows":
        return "definitions_list_flows"
    return route_id


def _route_doc(source: str, route_id: str, summaries: dict[str, str]) -> _RouteDoc:
    doc_id = _doc_route_id(source, route_id)
    return _RouteDoc(
        group=_SERVICE_GROUPS[source],
        summary=_resolve_summary(route_id, summaries),
        description=_DESCRIPTIONS.get(doc_id, _DESCRIPTIONS.get(route_id, "")),
        request_schema=_REQUEST_SCHEMAS.get(doc_id) or _REQUEST_SCHEMAS.get(route_id),
        query_schema=_QUERY_SCHEMAS.get(doc_id) or _QUERY_SCHEMAS.get(route_id),
        response_status=_RESPONSE_STATUS.get(doc_id, _RESPONSE_STATUS.get(route_id, 200)),
        route_id=doc_id,
    )


def _entry_to_definition(
    source: str,
    entry: definitions_routes.RouteEntry,
    summaries: dict[str, str],
) -> RouteDefinition:
    doc = _route_doc(source, entry.route_id, summaries)
    return RouteDefinition(
        route_id=doc.route_id or entry.route_id,
        method=entry.method,
        path=entry.path,
        group=doc.group,
        summary=doc.summary,
        description=doc.description,
        auth_required=entry.auth_required,
        request_schema=doc.request_schema,
        query_schema=doc.query_schema,
        response_status=doc.response_status,
    )


def meta_routes() -> tuple[RouteDefinition, ...]:
    """Meta discovery routes (health, OpenAPI, HTML docs)."""
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
    )


def collect_service_routes() -> tuple[RouteDefinition, ...]:
    """Project per-service ``ROUTES`` tuples into OpenAPI-oriented definitions."""
    summaries = _summary_index()
    sources: tuple[tuple[str, tuple[definitions_routes.RouteEntry, ...]], ...] = (
        ("assist", assist_routes.ROUTES),
        ("definitions", definitions_routes.ROUTES),
        ("flows", flows_routes.ROUTES),
        ("processes", processes_routes.ROUTES),
        ("providers", providers_routes.ROUTES),
        ("system", system_routes.ROUTES),
    )
    routes: list[RouteDefinition] = []
    for source, entries in sources:
        for entry in entries:
            routes.append(_entry_to_definition(source, entry, summaries))
    return tuple(routes)


def rest_routes() -> tuple[RouteDefinition, ...]:
    """Full REST surface for OpenAPI, HTML docs, and examples."""
    return meta_routes() + collect_service_routes()


__all__ = ["collect_service_routes", "meta_routes", "rest_routes"]