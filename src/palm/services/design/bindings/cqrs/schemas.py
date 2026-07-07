"""Design service CQRS schema definitions."""

from __future__ import annotations

from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.core.context.state_schema import DictStateSchema
from palm.services.design.bindings.cqrs.commands import (
    CommitDesignProposalCommand,
    DiscardDesignProposalCommand,
    ProposeFlowDefinitionCommand,
)
from palm.services.design.bindings.cqrs.queries import (
    AnalyzeDesignProposalImpactQuery,
    GetDesignProposalQuery,
    ListDesignProposalsQuery,
    ValidateDesignProposalQuery,
)

_STRING = {"type": "string", "minLength": 1}
_OPTIONAL_STRING: dict[str, object] = {}
_OBJECT = {"type": "object"}
_BOOL = {"type": "boolean"}

DESIGN_COMMAND_SCHEMAS = {
    ProposeFlowDefinitionCommand: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "body": _OBJECT,
                "base_flow_id": _OPTIONAL_STRING,
            },
            "required": ["body"],
        }
    ),
    CommitDesignProposalCommand: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "proposal_id": _STRING,
                "commit_token": _OPTIONAL_STRING,
                "input_token": _OPTIONAL_STRING,
            },
            "required": ["proposal_id"],
        }
    ),
    DiscardDesignProposalCommand: DictStateSchema(
        {
            "type": "object",
            "properties": {"proposal_id": _STRING},
            "required": ["proposal_id"],
        }
    ),
}

DESIGN_QUERY_SCHEMAS = {
    GetDesignProposalQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {"proposal_id": _STRING},
            "required": ["proposal_id"],
        }
    ),
    ListDesignProposalsQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {"flow_id": _OPTIONAL_STRING},
        }
    ),
    ValidateDesignProposalQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "proposal_id": _STRING,
                "dry_run": _BOOL,
            },
            "required": ["proposal_id"],
        }
    ),
    AnalyzeDesignProposalImpactQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {"proposal_id": _STRING},
            "required": ["proposal_id"],
        }
    ),
}


def register_design_cqrs_schemas(registry: CqrsSchemaRegistry) -> None:
    """Register design command/query schemas on ``registry``."""
    for command_type, schema in DESIGN_COMMAND_SCHEMAS.items():
        registry.register_command(command_type, schema)
    for query_type, schema in DESIGN_QUERY_SCHEMAS.items():
        registry.register_query(query_type, schema)


__all__ = [
    "DESIGN_COMMAND_SCHEMAS",
    "DESIGN_QUERY_SCHEMAS",
    "register_design_cqrs_schemas",
]