"""Explorer form schemas — :class:`~palm.core.context.state_schema.DictStateSchema` definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.context.state_schema import DictStateSchema

if TYPE_CHECKING:
    from palm.definitions.flow import FlowDefinition

_STRING = {"type": "string"}
_INTEGER = {"type": "integer", "minimum": 1, "maximum": 50}
_BOOL = {"type": "boolean"}

INLINE_WIZARD_FORM = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "wizard_name": {
                "type": "string",
                "title": "Wizard name",
                "description": "Inline wizard identifier (not from the repository)",
            },
            "wizard_steps": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 2,
                "title": "Step count",
                "description": "Number of wizard steps to run",
            },
        },
    }
)

# Backward-compatible static schema (tests and simple callers).
FLOW_SUBMIT_FORM = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "submit_mode": {
                "type": "string",
                "enum": ["registered", "inline_wizard"],
                "default": "registered",
                "title": "Submission mode",
            },
            "flow_id": _STRING,
            "flow_name": _STRING,
            "wizard_name": _STRING,
            "wizard_steps": _INTEGER,
            "job_id": {
                "type": "string",
                "title": "Job ID (optional)",
                "description": "Assign a custom job identifier",
            },
            "by_id": _BOOL,
        },
    }
)


def build_flow_submit_schema(flows: list[FlowDefinition]) -> DictStateSchema:
    """Build a context-aware submit schema from registered flows."""
    flow_ids = [flow.definition_id for flow in flows]
    flow_id_spec: dict[str, object] = {
        "type": "string",
        "title": "Registered flow",
        "description": "Select a flow from the repository",
        "x-placeholder": "Choose a flow…",
    }
    if flow_ids:
        flow_id_spec["enum"] = flow_ids

    return DictStateSchema(
        {
            "type": "object",
            "properties": {
                "submit_mode": {
                    "type": "string",
                    "enum": ["registered", "inline_wizard"],
                    "default": "registered",
                    "title": "Submission mode",
                    "description": "Start a registered definition or an inline wizard",
                },
                "flow_id": flow_id_spec,
                "wizard_name": {
                    "type": "string",
                    "title": "Test wizard name",
                    "description": "Label for a throwaway inline wizard (not from the repository)",
                },
                "wizard_steps": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 2,
                    "title": "Number of steps",
                    "description": "How many placeholder steps the test wizard should run",
                },
                "job_id": {
                    "type": "string",
                    "title": "Job ID (optional)",
                    "description": "Assign a custom job identifier",
                },
            },
        }
    )
