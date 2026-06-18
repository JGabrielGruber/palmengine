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
            "wizard_step_slug": _STRING,
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
    "ListJobsQuery": LIST_JOBS_QUERY,
    "ListInstancesQuery": LIST_INSTANCES_QUERY,
    "ListFlowsQuery": LIST_FLOWS_QUERY,
    "ListSnapshotsQuery": LIST_SNAPSHOTS_QUERY,
    "SnapshotSummary": SNAPSHOT_SUMMARY,
    "FlowSummary": FLOW_SUMMARY,
    "ProcessSummary": PROCESS_SUMMARY,
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
