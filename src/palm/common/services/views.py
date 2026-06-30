"""Service-layer view builders — stable dict shapes for user-facing APIs."""

from __future__ import annotations

from typing import Any

from palm.common.resource.catalog import ResourceCatalogEntry
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition


def flow_step_slugs(flow: FlowDefinition) -> list[str]:
    """Extract wizard step slugs from flow options when present."""
    options = flow.options or {}
    steps = options.get("steps")
    if not isinstance(steps, list):
        return []
    slugs: list[str] = []
    for step in steps:
        if isinstance(step, dict):
            slug = step.get("slug")
            if slug:
                slugs.append(str(slug))
    return slugs


def flow_summary(flow: FlowDefinition) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "flow_id": flow.definition_id,
        "name": flow.name,
        "pattern": flow.pattern,
        "has_state_schema": flow.has_state_schema,
    }
    slugs = flow_step_slugs(flow)
    if slugs:
        payload["step_slugs"] = slugs
    return payload


def flow_detail(flow: FlowDefinition) -> dict[str, Any]:
    return flow.to_dict()


def process_summary(process: ProcessDefinition) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "process_id": process.definition_id,
        "name": process.name,
        "storage": process.storage,
        "flow_count": len(process.flows),
    }
    metadata = process.metadata or {}
    entry_flow = metadata.get("entry_flow")
    if isinstance(entry_flow, str) and entry_flow:
        summary["entry_flow"] = entry_flow

    mcp = metadata.get("mcp")
    if isinstance(mcp, dict):
        entries = mcp.get("entries")
        if isinstance(entries, dict):
            fast = entries.get("fast")
            if isinstance(fast, dict):
                flow = fast.get("flow")
                if isinstance(flow, str) and flow:
                    summary["mcp_default_entry"] = flow
                submit = fast.get("submit")
                if isinstance(submit, str) and submit:
                    summary["submit_hint"] = submit
        default_entry = mcp.get("default_entry")
        if isinstance(default_entry, str) and default_entry:
            summary["mcp_default_entry_mode"] = default_entry

    if summary.get("entry_flow") or summary.get("mcp_default_entry"):
        summary.setdefault(
            "submit_hint",
            f'palm_submit_wizard(flow_name="{summary.get("mcp_default_entry") or entry_flow}")',
        )
        summary["avoid"] = "palm_submit_process (submits one job per flow)"

    return summary


def process_detail(process: ProcessDefinition) -> dict[str, Any]:
    return process.to_dict()


def resource_summary(entry: ResourceCatalogEntry) -> dict[str, Any]:
    return {
        "definition_id": entry.definition_id,
        "name": entry.name,
        "provider": entry.provider,
        "action": entry.action,
        "resource_id_template": entry.resource_id,
        "param_keys": list(entry.param_keys),
        "has_input_schema": entry.has_input_schema,
        "has_output_schema": entry.has_output_schema,
        "summary": entry.summary(),
    }


__all__ = [
    "flow_detail",
    "flow_step_slugs",
    "flow_summary",
    "process_detail",
    "process_summary",
    "resource_summary",
]