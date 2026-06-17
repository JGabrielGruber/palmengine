"""
REST documentation examples — curl commands and sample payloads.

Single source for served ``/v1/docs``, OpenAPI request examples, and static site copy.
"""

from __future__ import annotations

import json
from typing import Any

from palm.common.runtimes.server.middleware import PALM_SUBJECT_HEADER
from palm.runtimes.server.surfaces.rest.route_table import RouteDefinition, rest_routes

DEFAULT_BASE_URL = "http://localhost:8080"

PATH_PARAM_SAMPLES: dict[str, str] = {
    "job_id": "job-abc123",
    "instance_id": "inst-abc123",
    "snapshot_id": "0",
    "flow_id": "onboard",
    "process_id": "onboarding",
}

REQUEST_BODIES: dict[str, dict[str, Any]] = {
    "SubmitJobBody": {
        "flow_name": "onboard",
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
}

GROUP_DESCRIPTIONS: dict[str, str] = {
    "Meta": "Health, discovery, and API documentation.",
    "Jobs": "Orchestration job submission and interactive input.",
    "Plans": "Deferred plan staging and batch submission.",
    "Instances": "Durable process instance queries and resume.",
    "Snapshots": "Point-in-time blackboard captures for audit and replay.",
    "Catalog": "Registered flow and process definitions from the repository.",
}

RESPONSE_EXAMPLES: dict[str, Any] = {
    "health": {
        "status": "ok",
        "runtime": "ServerRuntime",
        "version": "0.12.0",
        "auth_enforce": False,
        "surfaces": ["rest"],
        "docs": "/v1/docs",
        "openapi": "/v1/openapi.json",
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
            "link": "/v1/instances/inst-abc123",
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
                "path": "/v1/jobs/job-abc123/input",
            }
        ],
    },
    "submit_job": {
        "job_id": "job-abc123",
        "status": "RUNNING",
        "metadata": {"pattern": "wizard"},
    },
    "provide_input": {
        "job_id": "job-abc123",
        "status": "RUNNING",
        "metadata": {"pattern": "wizard"},
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
    "get_instance": {
        "instance_id": "inst-abc123",
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "flow_name": "onboard",
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
                "wizard_step_slug": "name",
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
        "flows": [
            {
                "flow_id": "onboard",
                "name": "onboard",
                "pattern": "wizard",
                "has_state_schema": False,
            }
        ],
        "pagination": {"limit": 50, "offset": 0, "count": 1, "total": 1, "has_more": False},
    },
    "get_flow": {
        "version": 1,
        "kind": "flow",
        "name": "onboard",
        "pattern": "wizard",
        "options": {"steps": [{"slug": "name", "title": "Name", "prompt": "Your name?"}]},
    },
    "list_processes": {
        "processes": [
            {
                "process_id": "onboarding",
                "name": "onboarding",
                "storage": "memory",
                "flow_count": 1,
            }
        ],
        "pagination": {"limit": 50, "offset": 0, "count": 1, "total": 1, "has_more": False},
    },
    "get_process": {
        "version": 1,
        "kind": "process",
        "name": "onboarding",
        "storage": "memory",
        "flows": [{"name": "onboard", "pattern": "wizard", "options": {}}],
    },
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
        if route.route_id == "list_flows":
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
    featured_ids = (
        "health",
        "list_jobs",
        "get_job_context",
        "submit_job",
        "provide_input",
        "list_instances",
        "list_snapshots",
        "list_flows",
        "get_flow",
    )
    routes_by_id = {route.route_id: route for route in rest_routes()}
    examples: list[tuple[str, str, str]] = []
    for route_id in featured_ids:
        route = routes_by_id.get(route_id)
        if route is None:
            continue
        examples.append((route.summary, route.description, build_curl(route)))
    return examples
