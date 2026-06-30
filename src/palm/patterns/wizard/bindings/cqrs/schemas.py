"""Wizard CQRS schema definitions."""

from __future__ import annotations

from palm.core.context.state_schema import DictStateSchema
from palm.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
    SubmitWizardCommand,
)
from palm.patterns.wizard.bindings.cqrs.queries import (
    GetWizardProgressQuery,
    GetWizardStatusQuery,
    ListWizardProgressQuery,
)

_STRING = {"type": "string", "minLength": 1}
_OPTIONAL_STRING: dict[str, object] = {}
_OBJECT = {"type": "object"}
_ANY: dict[str, object] = {}
_BOOL = {"type": "boolean"}
_OPTIONAL: dict[str, object] = {}

WIZARD_COMMAND_SCHEMAS = {
    SubmitWizardCommand: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "body": _OBJECT,
                "runtime_name": _OPTIONAL_STRING,
            },
            "required": ["body"],
        }
    ),
    ProvideWizardInputCommand: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "instance_id": _STRING,
                "value": _ANY,
                "runtime_name": _OPTIONAL_STRING,
            },
            "required": ["instance_id", "value"],
        }
    ),
    RequestWizardBacktrackCommand: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "instance_id": _STRING,
                "to_step": _OPTIONAL_STRING,
                "runtime_name": _OPTIONAL_STRING,
            },
            "required": ["instance_id"],
        }
    ),
}

WIZARD_QUERY_SCHEMAS = {
    GetWizardProgressQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "instance_id": _OPTIONAL_STRING,
                "job_id": _OPTIONAL_STRING,
            },
        }
    ),
    GetWizardStatusQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {"instance_id": _STRING},
            "required": ["instance_id"],
        }
    ),
    ListWizardProgressQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "limit": _OPTIONAL,
                "active_only": _BOOL,
            },
        }
    ),
}

__all__ = ["WIZARD_COMMAND_SCHEMAS", "WIZARD_QUERY_SCHEMAS"]
