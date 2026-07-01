"""Generate assist + service command-path catalog for MCP resources."""

from __future__ import annotations

from typing import Any

from palm.services.assist.registry import assist_commands, list_mcp_path_aliases
from palm.services.definitions.registry import catalog_verbs
from palm.services.execution.flows.registry import flow_commands
from palm.services.execution.processes.registry import process_commands
from palm.services.execution.providers.registry import invoke_verbs
from palm.services.system.registry import observe_verbs


def build_assist_routes_catalog() -> dict[str, Any]:
    """Return machine-readable route catalog for ``palm://assist/routes``."""
    routes: list[dict[str, Any]] = []

    for command in assist_commands():
        routes.append(
            {
                "domain": "assist",
                "command_id": command.command_id,
                "path": list(command.path_pattern),
                "summary": command.summary,
            }
        )

    for command in flow_commands():
        routes.append(
            {
                "domain": "flows",
                "command_id": command.command_id,
                "path": list(command.path_pattern),
                "summary": command.summary,
            }
        )

    for command in process_commands():
        routes.append(
            {
                "domain": "processes",
                "command_id": command.command_id,
                "path": list(command.path_pattern),
                "summary": command.summary,
            }
        )

    for verb in catalog_verbs():
        routes.append(
            {
                "domain": "definitions",
                "command_id": verb.verb_id,
                "path": _definitions_path(verb),
                "summary": verb.summary,
            }
        )

    for verb in observe_verbs():
        routes.append(
            {
                "domain": "system",
                "command_id": verb.verb_id,
                "path": _system_path(verb.operation),
                "summary": verb.summary,
            }
        )

    for verb in invoke_verbs():
        routes.append(
            {
                "domain": "providers",
                "command_id": verb.verb_id,
                "path": _providers_path(verb.operation),
                "summary": verb.summary,
            }
        )

    aliases = list_mcp_path_aliases()
    return {
        "routes": routes,
        "aliases": aliases,
        "tool": "palm_assist",
        "usage": {
            "dispatch": 'palm_assist(path=["assist", "scenarios", "operator-entry", "start"], params={})',
            "alias": 'palm_assist(alias="operator-entry/start", params={})',
        },
    }


def _definitions_path(verb: Any) -> list[str]:
    kind = verb.resource_kind
    operation = verb.operation
    if operation == "list":
        return ["definitions", kind]
    if operation in {"get", "validate", "create", "update", "delete"}:
        suffix = "{id}" if operation != "validate" else "{flow_id}"
        if kind == "flows" and operation == "validate":
            return ["definitions", "flows", "validate"]
        return ["definitions", kind, suffix, operation] if operation != "get" else ["definitions", kind, "{id}"]
    return ["definitions", kind]


def _system_path(operation: str) -> list[str]:
    mapping = {
        "doctor": ["system", "doctor"],
        "list_jobs": ["system", "jobs"],
        "get_job": ["system", "jobs", "{job_id}"],
        "inspect_job": ["system", "jobs", "{job_id}", "context"],
        "list_instances": ["system", "instances"],
        "inspect_instance": ["system", "instances", "{instance_id}"],
        "instance_tree": ["system", "instances", "{instance_id}", "tree"],
        "list_snapshots": ["system", "instances", "{instance_id}", "snapshots"],
        "get_snapshot": ["system", "instances", "{instance_id}", "snapshots", "{snapshot_id}"],
        "resume_instance": ["system", "instances", "{instance_id}", "resume"],
        "cancel_job": ["system", "jobs", "{job_id}", "cancel"],
    }
    return mapping.get(operation, ["system", operation])


def _providers_path(operation: str) -> list[str]:
    if operation == "invoke":
        return ["providers", "{provider}", "{resource_ref}", "invoke"]
    if operation == "list":
        return ["providers"]
    return ["providers", "{provider}"]


__all__ = ["build_assist_routes_catalog"]