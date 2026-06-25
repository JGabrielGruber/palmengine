"""
REST request schemas — :class:`~palm.core.context.state_schema.DictStateSchema` definitions.

Schemas drive validation and OpenAPI component generation from a single source.
"""

from __future__ import annotations

from typing import Any

from palm.core.context.state_schema import DictStateSchema

# Shared fragments
_STRING = {"type": "string"}
_BOOL = {"type": "boolean"}
_OBJECT = {"type": "object"}
_ARRAY_OF_STRINGS = {"type": "array", "items": {"type": "string"}, "minItems": 1}

SUBMIT_JOB_BODY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "flow": _OBJECT,
            "wizard": _OBJECT,
            "flow_name": _STRING,
            "job_id": _STRING,
            "by_id": _BOOL,
        },
    }
)

SUBMIT_WIZARD_BODY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "flow": _OBJECT,
            "wizard": _OBJECT,
            "flow_name": _STRING,
            "job_id": _STRING,
            "by_id": _BOOL,
        },
    }
)

PREPARE_PLANS_BODY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "flow": _OBJECT,
            "wizard": _OBJECT,
            "flow_name": _STRING,
            "process": _OBJECT,
            "process_name": _STRING,
            "job_id": _STRING,
            "by_id": _BOOL,
        },
    }
)

SUBMIT_PLANS_BODY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "plan_ids": _ARRAY_OF_STRINGS,
        },
        "required": ["plan_ids"],
    }
)

PROVIDE_INPUT_BODY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "value": {},
        },
        "required": ["value"],
    }
)

WIZARD_INPUT_BODY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "value": {},
        },
        "required": ["value"],
    }
)

WIZARD_BACKTRACK_BODY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "to_step": _STRING,
        },
    }
)

LIST_JOBS_QUERY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "status": _STRING,
            "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            "offset": {"type": "integer", "minimum": 0},
        },
    }
)

LIST_INSTANCES_QUERY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "status": _STRING,
            "flow_name": _STRING,
            "include_terminal": _BOOL,
            "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            "offset": {"type": "integer", "minimum": 0},
        },
    }
)

LIST_FLOWS_QUERY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "pattern": _STRING,
            "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            "offset": {"type": "integer", "minimum": 0},
        },
    }
)

LIST_SNAPSHOTS_QUERY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            "offset": {"type": "integer", "minimum": 0},
        },
    }
)

SNAPSHOT_SUMMARY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "snapshot_id": _STRING,
            "status": _STRING,
            "recorded_at": _STRING,
            "job_id": _STRING,
            "current_step_slug": _STRING,
        },
    }
)

FLOW_SUMMARY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "flow_id": _STRING,
            "name": _STRING,
            "pattern": _STRING,
            "has_state_schema": _BOOL,
        },
    }
)

INVOKE_RESOURCE_BODY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "resource_ref": _STRING,
            "action": _STRING,
            "params": _OBJECT,
            "resource_id": _STRING,
            "state": _OBJECT,
        },
        "required": ["resource_ref"],
    }
)

PALM_INVOKE_PARAMS = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "wait": _BOOL,
            "wait_mode": {
                "type": "string",
                "enum": ["until_terminal", "until_input", "fire_and_forget"],
                "description": (
                    "How long to block on a child job. "
                    "until_terminal waits for SUCCESS/FAILED/CANCELLED (default when wait=true). "
                    "until_input returns when the child reaches WAITING_FOR_INPUT. "
                    "fire_and_forget submits and continues immediately."
                ),
            },
            "timeout_seconds": {"type": "number", "minimum": 0},
            "wait_timeout": {"type": "number", "minimum": 0},
            "flow_name": _STRING,
            "remote_url": _STRING,
            "max_depth": {"type": "integer", "minimum": 1},
        },
    }
)

PROCESS_SUMMARY = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "process_id": _STRING,
            "name": _STRING,
            "storage": _STRING,
            "flow_count": {"type": "integer", "minimum": 0},
        },
    }
)

# OpenAPI component names → schema instances
NAMED_SCHEMAS: dict[str, DictStateSchema] = {
    "SubmitJobBody": SUBMIT_JOB_BODY,
    "SubmitWizardBody": SUBMIT_WIZARD_BODY,
    "PreparePlansBody": PREPARE_PLANS_BODY,
    "SubmitPlansBody": SUBMIT_PLANS_BODY,
    "ProvideInputBody": PROVIDE_INPUT_BODY,
    "WizardInputBody": WIZARD_INPUT_BODY,
    "WizardBacktrackBody": WIZARD_BACKTRACK_BODY,
    "ListJobsQuery": LIST_JOBS_QUERY,
    "ListInstancesQuery": LIST_INSTANCES_QUERY,
    "ListFlowsQuery": LIST_FLOWS_QUERY,
    "ListSnapshotsQuery": LIST_SNAPSHOTS_QUERY,
    "SnapshotSummary": SNAPSHOT_SUMMARY,
    "FlowSummary": FLOW_SUMMARY,
    "ProcessSummary": PROCESS_SUMMARY,
    "PalmInvokeParams": PALM_INVOKE_PARAMS,
    "InvokeResourceBody": INVOKE_RESOURCE_BODY,
}


def openapi_components() -> dict[str, Any]:
    """Export schema documents for OpenAPI ``components.schemas``."""
    return {name: schema.definition for name, schema in NAMED_SCHEMAS.items()}


def submit_job_variant_errors(body: dict[str, Any]) -> list[str]:
    """Require exactly one flow submission style in the request body."""
    return _single_variant_errors(body, ("flow", "wizard", "flow_name"))


def submit_wizard_variant_errors(body: dict[str, Any]) -> list[str]:
    """Require exactly one wizard submission style in the request body."""
    return _single_variant_errors(body, ("flow", "wizard", "flow_name"))


def _single_variant_errors(body: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    present = [key for key in keys if key in body]
    if len(present) == 1:
        return []
    if not present:
        return [f"one of {list(keys)} is required"]
    return [f"provide only one of {list(keys)}; found {present}"]


def prepare_plans_variant_errors(body: dict[str, Any]) -> list[str]:
    """Require a recognizable plan preparation payload."""
    flow_keys = ("flow", "wizard", "flow_name")
    process_keys = ("process", "process_name")
    if any(key in body for key in process_keys):
        return []
    if any(key in body for key in flow_keys):
        return []
    return ["expected 'process', 'process_name', or a flow submission payload"]
