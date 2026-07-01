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
    "snapshot_id": "0",
    "flow_id": "onboard",
    "process_id": "onboarding",
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
    "Jobs": "Orchestration job submission and interactive input.",
    "Plans": "Deferred plan staging and batch submission.",
    "Instances": "Durable process instance queries and resume.",
    "Snapshots": "Point-in-time blackboard captures for audit and replay.",
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
    "submit_wizard": {
        "instance_id": "inst-abc123",
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "metadata": {"pattern": "wizard"},
    },
    "get_wizard": {
        "instance_id": "inst-abc123",
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "flow_name": "todo-builder",
        "current_step_slug": "todos",
        "wizard_progress": {
            "current_step": "todos",
            "completed_steps": [],
        },
        "prompt": {
            "step": "todos",
            "title": "Todo List",
            "text": "Manage your todos — add items, edit/remove, then continue.",
            "step_kind": "collection",
            "collection_phase": "menu",
            "collection_items": [{"title": "Buy milk", "priority": "high"}],
            "label_field": "title",
            "min_items": 1,
        },
        "answers": {},
        "committed": False,
        "links": {
            "self": "/v1/wizards/inst-abc123",
            "instance": "/v1/instances/inst-abc123",
            "job": "/v1/jobs/job-abc123",
        },
        "next_actions": [
            {
                "action": "provide_wizard_input",
                "method": "POST",
                "path": "/v1/wizards/inst-abc123/input",
            },
            {
                "action": "request_backtrack",
                "method": "POST",
                "path": "/v1/wizards/inst-abc123/backtrack",
            },
        ],
    },
    "provide_wizard_input": {
        "instance_id": "inst-abc123",
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "slug": "step_2",
        "prompt": {
            "step": "step_2",
            "text": "Step 2?",
        },
        "answers": {"step_1": "Ada Lovelace"},
        "next_actions": [
            {
                "action": "provide_wizard_input",
                "method": "POST",
                "path": "/v1/wizards/inst-abc123/input",
            }
        ],
    },
    "backtrack_wizard": {
        "instance_id": "inst-abc123",
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "to_step": "step_1",
        "prompt": {
            "step": "step_1",
            "text": "Step 1?",
        },
        "answers": {},
    },
    "resume_child_wait": {
        "instance_id": "inst-abc123",
        "job_id": "job-abc123",
        "status": "WAITING_FOR_INPUT",
        "current_step_slug": "resource_step",
        "waiting_for_child": False,
    },
    "resume_wizard_tick": {
        "instance_id": "inst-abc123",
        "job_id": "job-abc123",
        "status": "RUNNING",
        "current_step_slug": "fetch_customer",
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
    "validate_flow": {
        "valid": True,
        "pattern": "wizard",
        "flow": "onboard",
        "step_slugs": ["name", "confirm"],
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
    "list_resources": {
        "resources": [
            {
                "definition_id": "fetch-customer",
                "name": "fetch-customer",
                "provider": "rest",
                "action": "fetch",
                "param_keys": ["customer_id"],
                "has_input_schema": True,
                "has_output_schema": True,
            }
        ],
        "pagination": {"limit": 50, "offset": 0, "count": 1, "total": 1, "has_more": False},
    },
    "get_resource": {
        "definition_id": "fetch-customer",
        "name": "fetch-customer",
        "provider": "rest",
        "action": "fetch",
        "params": {"customer_id": {"type": "string", "required": True}},
        "summary": "Fetch customer record via REST provider",
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
    )
    routes_by_id = {route.route_id: route for route in rest_routes()}
    examples: list[tuple[str, str, str]] = []
    for route_id in featured_ids:
        route = routes_by_id.get(route_id)
        if route is None:
            continue
        examples.append((route.summary, route.description, build_curl(route)))
    return examples
