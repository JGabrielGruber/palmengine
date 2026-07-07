"""
Core CQRS command/query schema registration.
"""

from __future__ import annotations

from palm.common.cqrs.command import (
    CancelJobCommand,
    MigrateInstanceCommand,
    PreparePlansCommand,
    ProvideInputCommand,
    ResumeProcessCommand,
    SubmitFlowCommand,
    SubmitPlansCommand,
    SubmitProcessCommand,
)
from palm.common.cqrs.query import (
    AnalyzeDefinitionImpactQuery,
    GetFlowQuery,
    GetInstanceSnapshotQuery,
    GetInstanceStatusQuery,
    GetJobContextQuery,
    GetJobStatusQuery,
    GetProcessQuery,
    GetResourceInvocationsQuery,
    InspectInstanceQuery,
    ListFlowsQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
    ListProcessesQuery,
    ListResourceInvocationsQuery,
)
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.core.context.state_schema import DictStateSchema

_STRING = {"type": "string", "minLength": 1}
_OPTIONAL_STRING: dict[str, object] = {}
_BOOL = {"type": "boolean"}
_OBJECT = {"type": "object"}
_ANY: dict[str, object] = {}
_INT = {"type": "integer", "minimum": 1}
_OPTIONAL: dict[str, object] = {}
_ARRAY_STRINGS = {"type": "array", "items": {"type": "string"}, "minItems": 1}


def register_core_schemas(registry: CqrsSchemaRegistry) -> None:
    """Register schemas for host-level commands and queries."""
    registry.register_command(
        SubmitFlowCommand,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "flow": _ANY,
                    "runtime_name": _OPTIONAL_STRING,
                    "by_id": _BOOL,
                    "job_id": _OPTIONAL_STRING,
                    "state": _ANY,
                    "metadata": _OBJECT,
                },
                "required": ["flow"],
            }
        ),
    )
    registry.register_command(
        SubmitProcessCommand,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "process": _ANY,
                    "runtime_name": _OPTIONAL_STRING,
                    "by_id": _BOOL,
                    "job_id": _OPTIONAL_STRING,
                    "state": _ANY,
                    "metadata": _OBJECT,
                },
                "required": ["process"],
            }
        ),
    )
    registry.register_command(
        ProvideInputCommand,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "job_id": _STRING,
                    "value": _ANY,
                    "runtime_name": _OPTIONAL_STRING,
                },
                "required": ["job_id", "value"],
            }
        ),
    )
    registry.register_command(
        ResumeProcessCommand,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "instance_id": _STRING,
                    "runtime_name": _OPTIONAL_STRING,
                },
                "required": ["instance_id"],
            }
        ),
    )
    registry.register_command(
        PreparePlansCommand,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "body": _OBJECT,
                    "runtime_name": _OPTIONAL_STRING,
                },
                "required": ["body"],
            }
        ),
    )
    registry.register_command(
        SubmitPlansCommand,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "plan_ids": _ARRAY_STRINGS,
                    "runtime_name": _OPTIONAL_STRING,
                },
                "required": ["plan_ids"],
            }
        ),
    )
    registry.register_command(
        CancelJobCommand,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "job_id": _STRING,
                    "runtime_name": _OPTIONAL_STRING,
                },
                "required": ["job_id"],
            }
        ),
    )
    registry.register_command(
        MigrateInstanceCommand,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "instance_id": _STRING,
                    "target_revision": _INT,
                    "dry_run": _BOOL,
                },
                "required": ["instance_id", "target_revision"],
            }
        ),
    )

    registry.register_query(
        ListInstancesQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "status": _OPTIONAL_STRING,
                    "flow_name": _OPTIONAL_STRING,
                    "include_terminal": _BOOL,
                    "limit": _OPTIONAL,
                },
            }
        ),
    )
    registry.register_query(
        GetInstanceStatusQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {"instance_id": _STRING},
                "required": ["instance_id"],
            }
        ),
    )
    registry.register_query(
        ListInstanceSnapshotsQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {"instance_id": _STRING},
                "required": ["instance_id"],
            }
        ),
    )
    registry.register_query(
        GetInstanceSnapshotQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "instance_id": _STRING,
                    "snapshot_id": _STRING,
                },
                "required": ["instance_id", "snapshot_id"],
            }
        ),
    )
    registry.register_query(
        ListJobStatusQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "status": _OPTIONAL_STRING,
                    "limit": _OPTIONAL,
                },
            }
        ),
    )
    registry.register_query(
        GetJobStatusQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {"job_id": _STRING},
                "required": ["job_id"],
            }
        ),
    )
    registry.register_query(
        GetJobContextQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {"job_id": _STRING},
                "required": ["job_id"],
            }
        ),
    )
    registry.register_query(
        InspectInstanceQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {"instance_id": _STRING},
                "required": ["instance_id"],
            }
        ),
    )
    registry.register_query(
        ListFlowsQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {"pattern": _OPTIONAL_STRING},
            }
        ),
    )
    registry.register_query(
        GetFlowQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "flow_id": _STRING,
                    "revision": {"type": ["integer", "null"]},
                },
                "required": ["flow_id"],
            }
        ),
    )
    registry.register_query(
        AnalyzeDefinitionImpactQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "flow_id": _STRING,
                    "target_revision": {"type": ["integer", "null"]},
                },
                "required": ["flow_id"],
            }
        ),
    )
    registry.register_query(
        ListProcessesQuery,
        DictStateSchema({"type": "object", "properties": {}}),
    )
    registry.register_query(
        GetProcessQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {"process_id": _STRING},
                "required": ["process_id"],
            }
        ),
    )
    registry.register_query(
        GetResourceInvocationsQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {
                    "instance_id": _OPTIONAL_STRING,
                    "job_id": _OPTIONAL_STRING,
                },
            }
        ),
    )
    registry.register_query(
        ListResourceInvocationsQuery,
        DictStateSchema(
            {
                "type": "object",
                "properties": {"limit": _OPTIONAL},
            }
        ),
    )


__all__ = ["register_core_schemas"]
