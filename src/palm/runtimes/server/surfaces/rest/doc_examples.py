"""
REST documentation examples — curl commands and sample payloads.

Single source for served ``/v1/docs``, OpenAPI request examples, and static site copy.
"""

from __future__ import annotations

import json
from typing import Any

from palm import __version__
from palm.common.runtimes.server.middleware import PALM_SUBJECT_HEADER
from palm.runtimes.server.surfaces.rest.route_table import RouteDefinition, rest_routes

DEFAULT_BASE_URL = "http://localhost:8080"

PATH_PARAM_SAMPLES: dict[str, str] = {
    "job_id": "job-abc123",
    "instance_id": "inst-abc123",
    "session_id": "inst-abc123",
    "snapshot_id": "0",
    "flow_id": "onboard",
    "process_id": "onboarding",
    "provider": "rest",
    "resource_ref": "health/check",
}

REQUEST_BODIES: dict[str, dict[str, Any]] = {
    "SubmitJobBody": {
        "flow_name": "onboard",
    },
    "SubmitWizardBody": {
        "wizard": {"name": "onboard", "steps": 3},
    },
    "PreparePlansBody": {
        "process_name": "pipeline",
    },
    "SubmitPlansBody": {
        "plan_ids": ["plan-abc123"],
    },
    "ProvideInputBody": {
        "value": "Ada Lovelace",
    },
    "WizardInputBody": {
        "value": "Ada Lovelace",
    },
    "WizardBacktrackBody": {
        "to_step": "name",
    },
    "ValidateFlowBody": {
        "flow_name": "onboard",
    },
}

OPENAPI_REQUEST_EXAMPLES: dict[str, dict[str, dict[str, Any]]] = {
    "SubmitJobBody": {
        "wizard": {
            "summary": "Submit a wizard flow",
            "value": {"wizard": {"name": "onboard", "steps": 3}},
        },
        "flow_name": {
            "summary": "Submit by repository name",
            "value": {"flow_name": "my_flow"},
        },
    },
    "SubmitWizardBody": {
        "wizard": {
            "summary": "Inline wizard definition",
            "value": {"wizard": {"name": "onboard", "steps": 3}},
        },
        "flow_name": {
            "summary": "Submit registered wizard by name",
            "value": {"flow_name": "onboard"},
        },
    },
    "PreparePlansBody": {
        "process": {
            "summary": "Stage a multi-flow process",
            "value": {
                "process": {
                    "name": "pipeline",
                    "flows": [
                        {"name": "extract", "pattern": "etl"},
                        {"name": "graph", "pattern": "dag"},
                    ],
                }
            },
        },
    },
    "SubmitPlansBody": {
        "default": {
            "summary": "Submit staged plan ids",
            "value": {"plan_ids": ["plan-abc123", "plan-def456"]},
        },
    },
    "ProvideInputBody": {
        "default": {
            "summary": "Answer a wizard prompt",
            "value": {"value": "Ada Lovelace"},
        },
    },
    "WizardInputBody": {
        "scalar": {
            "summary": "Answer a text prompt",
            "value": {"value": "Ada Lovelace"},
        },
        "collection_menu": {
            "summary": "Collection menu — add a new item",
            "value": {"value": "Add a new item"},
        },
        "collection_field": {
            "summary": "Collection field — save item title",
            "value": {"value": "Buy milk"},
        },
        "collection_done": {
            "summary": "Collection menu — continue to summary",
            "value": {"value": "Continue to summary"},
        },
    },
    "WizardBacktrackBody": {
        "explicit": {
            "summary": "Backtrack to a named step",
            "value": {"to_step": "name"},
        },
        "previous": {
            "summary": "Backtrack to the previous step",
            "value": {},
        },
    },
}

GROUP_DESCRIPTIONS: dict[str, str] = {
    "Meta": "Health, discovery, and API documentation.",
    "System": "Observe, diagnose, and lifecycle orchestration state.",
    "Flows": "Interactive flow sessions — create, input, backtrack, resume.",
    "Processes": "Multi-flow process staging and submission.",
    "Providers": "Provider resource invocation.",
    "Definitions": "Flow, process, and resource definition catalog.",
}

RESPONSE_EXAMPLES: dict[str, Any] = {
    "health": {
        "status": "ok",
        "runtime": "ServerRuntime",
        "version": __version__,
        "auth_enforce": False,
        "surfaces": ["rest"],
        "docs": "/v1/docs",
        "openapi": "/v1/openapi.json",
    },
    "doctor": {
        "status": "ok",
        "version": __version__,
        "runtime": "ServerRuntime",
        "auth_enforce": False,
        "storage": {"backend": "memory", "open": True},
        "registries": {
            "patterns": ["wizard", "parallel", "pipeline"],
            "providers": ["palm", "rest"],
            "storages": ["memory"],
            "transforms": ["enrich_resource"],
        },
        "resource_count": 2,
        "jobs": {"total": 1, "waiting_for_input": 0},
        "issues": [],
    },
    "openapi": {"openapi": "3.0.3", "info": {"title": "Palm Engine API"}},
    "docs": "(HTML documentation page)",
    "list_jobs": {
        "jobs": [
            {
                "job_id": "job-abc123",
                "status": "WAITING_FOR_INPUT",
                "metadata": {"pattern": "wizard"},
            }
        ],
        "pagination": {"limit": 50, "offset": 0, "count": 1, "total": 1, "has_more": False},
    },
    "get_job": {
        "found": True,
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "metadata": {"pattern": "wizard"},
        "step": "name",
    },
    "inspect_job": {
        "found": True,
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "metadata": {"pattern": "wizard"},
        "pattern": {
            "pattern": "wizard",
            "step": "name",
            "prompt": "Your name?",
            "answers": {},
        },
        "instance": {
            "instance_id": "inst-abc123",
            "link": "/v1/api/system/instances/inst-abc123",
            "status": "WAITING_FOR_INPUT",
        },
        "wizard_progress": {
            "current_step": "name",
            "completed_steps": [],
        },
        "blackboard_snapshot": None,
        "recent_events": [],
        "next_actions": [
            {
                "action": "provide_input",
                "method": "POST",
                "path": "/v1/api/flows/onboard/session/inst-abc123/input",
            }
        ],
    },
    "get_job_context": {
        "found": True,
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "metadata": {"pattern": "wizard"},
        "pattern": {
            "pattern": "wizard",
            "step": "name",
            "prompt": "Your name?",
            "answers": {},
        },
        "instance": {
            "instance_id": "inst-abc123",
            "link": "/v1/api/system/instances/inst-abc123",
            "status": "WAITING_FOR_INPUT",
        },
        "wizard_progress": {
            "current_step": "name",
            "completed_steps": [],
        },
        "blackboard_snapshot": None,
        "recent_events": [],
        "next_actions": [
            {
                "action": "provide_input",
                "method": "POST",
                "path": "/v1/api/flows/onboard/session/inst-abc123/input",
            }
        ],
    },
    "submit_job": {
        "job_id": "job-abc123",
        "status": "RUNNING",
        "metadata": {"pattern": "wizard"},
    },
    "invoke_resource": {
        "success": True,
        "data": {
            "id": "health/check",
            "source": "rest",
            "status_code": 200,
            "body": {"ok": True},
        },
        "error": None,
        "metadata": {"action": "fetch", "provider": "rest"},
    },
    "provide_input": {
        "job_id": "job-abc123",
        "status": "RUNNING",
        "metadata": {"pattern": "wizard"},
    },
    "cancel_job": {
        "job_id": "job-abc123",
        "cancelled": True,
        "status": "CANCELLED",
    },
    "prepare_plans": {
        "plans": [
            {
                "plan_id": "plan-abc123",
                "kind": "flow",
                "flow_name": "onboard",
                "expires_at": "2026-06-17T13:00:00+00:00",
            }
        ]
    },
    "submit_plans": {
        "jobs": [{"job_id": "job-abc123", "status": "RUNNING", "metadata": {}}],
    },
    "list_instances": {
        "instances": [
            {
                "instance_id": "inst-abc123",
                "job_id": "job-abc123",
                "status": "WAITING_FOR_INPUT",
                "flow_name": "onboard",
            }
        ],
        "pagination": {"limit": 50, "offset": 0, "count": 1, "total": 1, "has_more": False},
    },
    "inspect_instance": {
        "instance_id": "inst-abc123",
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "flow_name": "onboard",
    },
    "get_instance": {
        "instance_id": "inst-abc123",
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "flow_name": "onboard",
    },
    "instance_tree": {
        "instance_id": "inst-abc123",
        "root": {
            "instance_id": "inst-abc123",
            "job_id": "job-abc123",
            "flow": "parent-wizard",
            "status": "WAITING_FOR_INPUT",
        },
        "ancestors": [],
        "active_child": None,
        "links": {
            "explorer": "http://localhost:8080/explorer/instances/inst-abc123",
            "session": "/v1/api/flows/parent-wizard/session/inst-abc123",
        },
    },
    "get_instance_tree": {
        "instance_id": "inst-abc123",
        "root": {
            "instance_id": "inst-abc123",
            "job_id": "job-abc123",
            "flow": "parent-wizard",
            "status": "WAITING_FOR_INPUT",
        },
        "ancestors": [],
        "active_child": {
            "instance_id": "inst-child456",
            "job_id": "job-child456",
            "flow": "child-wizard",
            "status": "WAITING_FOR_INPUT",
        },
        "links": {
            "explorer": "http://localhost:8080/explorer/instances/inst-abc123",
            "session": "/v1/api/flows/parent-wizard/session/inst-abc123",
        },
    },
    "resume_instance": {
        "job_id": "job-abc123",
        "status": "RUNNING",
        "instance_id": "inst-abc123",
    },
    "list_snapshots": {
        "snapshots": [
            {
                "snapshot_id": "0",
                "status": "WAITING_FOR_INPUT",
                "recorded_at": "2026-06-17T12:00:00+00:00",
                "job_id": "job-abc123",
                "current_step_slug": "name",
            }
        ],
        "pagination": {"limit": 50, "offset": 0, "count": 1, "total": 1, "has_more": False},
    },
    "get_snapshot": {
        "snapshot_id": "0",
        "status": "WAITING_FOR_INPUT",
        "recorded_at": "2026-06-17T12:00:00+00:00",
        "job_id": "job-abc123",
        "state_snapshot": {"answers": {"name": "Ada"}},
    },
    "list_flows": {
        "flows": [{"flow_id": "onboard", "pattern": "wizard"}],
        "pagination": {"limit": 50, "offset": 0, "count": 1, "total": 1, "has_more": False},
    },
    "definitions_list_flows": {
        "flows": [{"flow_id": "onboard", "pattern": "wizard"}],
        "pagination": {"limit": 50, "offset": 0, "count": 1, "total": 1, "has_more": False},
    },
    "describe_flow": {"flow_id": "onboard", "pattern": "wizard", "steps": 3},
    "create_session": {
        "session_id": "inst-abc123",
        "job_id": "job-abc123",
        "status": "RUNNING",
    },
    "get_session": {
        "session_id": "inst-abc123",
        "flow_id": "onboard",
        "status": "WAITING_FOR_INPUT",
        "step": "name",
    },
    "session_input": {
        "session_id": "inst-abc123",
        "status": "RUNNING",
        "step": "email",
    },
    "session_backtrack": {
        "session_id": "inst-abc123",
        "status": "WAITING_FOR_INPUT",
        "step": "name",
    },
    "session_resume": {
        "session_id": "inst-abc123",
        "status": "RUNNING",
    },
    "session_resume_child_wait": {
        "session_id": "inst-abc123",
        "status": "RUNNING",
        "waiting_for_child": False,
    },
    "session_cancel": {
        "session_id": "inst-abc123",
        "status": "CANCELLED",
    },
    "prepare_process": {
        "plans": [
            {
                "plan_id": "plan-abc123",
                "kind": "flow",
                "flow_name": "onboard",
                "expires_at": "2026-06-17T13:00:00+00:00",
            }
        ]
    },
    "submit_process": {
        "jobs": [{"job_id": "job-abc123", "status": "RUNNING", "metadata": {}}],
    },
    "run_process": {
        "jobs": [{"job_id": "job-abc123", "status": "RUNNING", "metadata": {}}],
    },
    "invoke_provider": {
        "success": True,
        "data": {"ok": True},
        "error": None,
        "metadata": {"action": "fetch", "provider": "rest"},
    },
    "get_flow": {"flow_id": "onboard", "pattern": "wizard"},
    "create_flow": {"saved": True, "kind": "flow", "flow": {"flow_id": "onboard"}},
    "update_flow": {"saved": True, "kind": "flow", "flow": {"flow_id": "onboard"}},
    "delete_flow": {"deleted": True, "kind": "flow", "flow_id": "onboard"},
    "validate_flow": {"valid": True, "flow_id": "onboard"},
    "list_processes": {
        "processes": [{"process_id": "pipeline"}],
        "pagination": {"limit": 50, "offset": 0, "count": 1, "total": 1, "has_more": False},
    },
    "get_process": {"process_id": "pipeline", "flows": ["extract", "graph"]},
    "create_process": {"saved": True, "kind": "process", "process": {"process_id": "pipeline"}},
    "update_process": {"saved": True, "kind": "process", "process": {"process_id": "pipeline"}},
    "delete_process": {"deleted": True, "kind": "process", "process_id": "pipeline"},
    "list_resources": {
        "resources": [{"resource_ref": "health/check", "provider": "rest"}],
        "pagination": {"limit": 50, "offset": 0, "count": 1, "total": 1, "has_more": False},
    },
    "get_resource": {"resource_ref": "health/check", "provider": "rest"},
    "create_resource": {
        "saved": True,
        "kind": "resource",
        "resource": {"resource_ref": "health/check"},
    },
    "update_resource": {
        "saved": True,
        "kind": "resource",
        "resource": {"resource_ref": "health/check"},
    },
    "delete_resource": {"deleted": True, "kind": "resource", "resource_ref": "health/check"},
}

_RESPONSE_ALIASES: dict[str, str] = {
    "get_job_context": "inspect_job",
    "get_instance": "inspect_instance",
    "prepare_plans": "prepare_process",
    "submit_plans": "submit_process",
    "submit_job": "create_session",
    "provide_input": "session_input",
    "invoke_resource": "invoke_provider",
}

QUERY_HINTS: dict[str, str] = {
    "ListJobsQuery": "status, limit, offset",
    "ListInstancesQuery": "status, flow_name, include_terminal, limit, offset",
    "ListFlowsQuery": "pattern, limit, offset",
    "ListSnapshotsQuery": "limit, offset",
}


def resolve_path(path: str) -> str:
    """Substitute example values for path parameters."""
    resolved = path
    for key, value in PATH_PARAM_SAMPLES.items():
        resolved = resolved.replace(f"{{{key}}}", value)
    return resolved


def build_curl(
    route: RouteDefinition,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> str:
    """Build a copyable curl command for a route."""
    url = f"{base_url}{resolve_path(route.path)}"
    if route.query_schema and route.method == "GET":
        url = f"{url}?limit=10&offset=0"
        if route.route_id in ("list_flows", "definitions_list_flows"):
            url = f"{url}&pattern=wizard"
        if route.route_id == "list_instances":
            url = f"{url}&include_terminal=true"

    lines = [f"curl -s -X {route.method} '{url}'"]
    lines.append("  -H 'Accept: application/json'")

    if route.auth_required:
        lines.append(f"  -H '{PALM_SUBJECT_HEADER}: dev'")

    if route.request_schema:
        body = REQUEST_BODIES.get(route.request_schema, {})
        payload = json.dumps(body, separators=(",", ":"))
        lines.append("  -H 'Content-Type: application/json'")
        lines.append(f"  -d '{payload}'")

    return " \\\n".join(lines)


def response_example(route: RouteDefinition) -> str:
    """Pretty-printed sample response for documentation."""
    sample = RESPONSE_EXAMPLES.get(route.route_id)
    if sample is None:
        sample = RESPONSE_EXAMPLES.get(_RESPONSE_ALIASES.get(route.route_id, ""))
    if sample is None:
        return ""
    if isinstance(sample, str):
        return sample
    return json.dumps(sample, indent=2)


def schema_fields(schema_name: str) -> list[str]:
    """Return human-readable schema field highlights."""
    from palm.runtimes.server.surfaces.rest.schemas import NAMED_SCHEMAS

    schema = NAMED_SCHEMAS.get(schema_name)
    if schema is None:
        return []
    definition = schema.definition
    properties = definition.get("properties") or {}
    required = set(definition.get("required") or [])
    fields: list[str] = []
    for name in properties:
        marker = "required" if name in required else "optional"
        fields.append(f"{name} ({marker})")
    return fields


def featured_curl_examples() -> list[tuple[str, str, str]]:
    """Return (title, description, curl) tuples for static site and quick reference."""
    featured_ids = ("health",)
    routes_by_id = {route.route_id: route for route in rest_routes()}
    examples: list[tuple[str, str, str]] = []
    for route_id in featured_ids:
        route = routes_by_id.get(route_id)
        if route is None:
            continue
        examples.append((route.summary, route.description, build_curl(route)))

    base = DEFAULT_BASE_URL
    examples.extend(
        [
            (
                "List jobs",
                "Paginated orchestration job board under the system service.",
                f"curl -s -X GET '{base}/v1/api/system/jobs?limit=10&offset=0' \\\n"
                "  -H 'Accept: application/json'",
            ),
            (
                "Get job context",
                "Rich job view with pattern state, wizard progress, and next actions.",
                f"curl -s -X GET '{base}/v1/api/system/jobs/job-abc123/context' \\\n"
                "  -H 'Accept: application/json'",
            ),
            (
                "Create flow session",
                "Start an interactive wizard session via the flows service.",
                f"curl -s -X POST '{base}/v1/api/flows/onboard/create' \\\n"
                "  -H 'Accept: application/json' \\\n"
                "  -H 'Content-Type: application/json' \\\n"
                "  -d '{{\"wizard\":{{\"name\":\"onboard\",\"steps\":3}}}}'",
            ),
            (
                "List instances",
                "Durable process instance index under the system service.",
                f"curl -s -X GET '{base}/v1/api/system/instances?limit=10&offset=0' \\\n"
                "  -H 'Accept: application/json'",
            ),
            (
                "List snapshots",
                "Point-in-time state snapshots for a durable instance.",
                f"curl -s -X GET '{base}/v1/api/system/instances/inst-abc123/snapshots?limit=10' \\\n"
                "  -H 'Accept: application/json'",
            ),
            (
                "Prepare process plans",
                "Stage execution plans for a multi-flow process.",
                f"curl -s -X POST '{base}/v1/api/processes/pipeline/prepare' \\\n"
                "  -H 'Accept: application/json' \\\n"
                "  -H 'Content-Type: application/json' \\\n"
                "  -d '{{\"process_name\":\"pipeline\"}}'",
            ),
        ]
    )
    return examples
