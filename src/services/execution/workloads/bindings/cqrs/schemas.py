"""Workload CQRS schemas."""

from __future__ import annotations

from palm.core.context.state_schema import DictStateSchema
from services.execution.workloads.bindings.cqrs.commands import (
    CancelWorkloadCommand,
    ExecWorkloadCommand,
    StartWorkloadCommand,
    StopWorkloadCommand,
)
from services.execution.workloads.bindings.cqrs.queries import (
    GetWorkloadQuery,
    ListWorkloadHostsQuery,
    ListWorkloadRuntimesQuery,
    ListWorkloadsQuery,
)

_STRING = {"type": "string", "minLength": 1}
_OPTIONAL_STRING: dict[str, object] = {}
_OBJECT = {"type": "object"}
_BOOL = {"type": "boolean"}
_ARRAY = {"type": "array"}
_NUMBER: dict[str, object] = {}

WORKLOAD_COMMAND_SCHEMAS = {
    StartWorkloadCommand: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "spec": _OBJECT,
                "owner": _OBJECT,
                "workload_id": _OPTIONAL_STRING,
                "idempotency_key": _OPTIONAL_STRING,
                "host_id": _OPTIONAL_STRING,
                "runtime_name": _OPTIONAL_STRING,
            },
            "required": ["spec"],
        }
    ),
    ExecWorkloadCommand: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "workload_id": _STRING,
                "command": _ARRAY,
                "timeout_s": _NUMBER,
                "env": _OBJECT,
                "runtime_name": _OPTIONAL_STRING,
            },
            "required": ["workload_id", "command"],
        }
    ),
    StopWorkloadCommand: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "workload_id": _STRING,
                "runtime_name": _OPTIONAL_STRING,
            },
            "required": ["workload_id"],
        }
    ),
    CancelWorkloadCommand: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "workload_id": _STRING,
                "runtime_name": _OPTIONAL_STRING,
            },
            "required": ["workload_id"],
        }
    ),
}

WORKLOAD_QUERY_SCHEMAS = {
    GetWorkloadQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "workload_id": _STRING,
                "refresh": _BOOL,
                "runtime_name": _OPTIONAL_STRING,
            },
            "required": ["workload_id"],
        }
    ),
    ListWorkloadsQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {
                "job_id": _OPTIONAL_STRING,
                "instance_id": _OPTIONAL_STRING,
                "session_id": _OPTIONAL_STRING,
                "status": _OPTIONAL_STRING,
                "runtime": _OPTIONAL_STRING,
                "runtime_name": _OPTIONAL_STRING,
            },
        }
    ),
    ListWorkloadHostsQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {"runtime_name": _OPTIONAL_STRING},
        }
    ),
    ListWorkloadRuntimesQuery: DictStateSchema(
        {
            "type": "object",
            "properties": {"runtime_name": _OPTIONAL_STRING},
        }
    ),
}

__all__ = ["WORKLOAD_COMMAND_SCHEMAS", "WORKLOAD_QUERY_SCHEMAS"]
