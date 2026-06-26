"""REST serializers — definition and snapshot response shapes."""

from __future__ import annotations

from typing import Any

from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.instances import StateSnapshot


def snapshot_summary(index: int, snapshot: StateSnapshot) -> dict[str, Any]:
    return {
        "snapshot_id": str(index),
        "status": snapshot.status,
        "recorded_at": snapshot.recorded_at,
        "job_id": snapshot.job_id,
        "current_step_slug": snapshot.current_step_slug,
    }


def snapshot_detail(index: int, snapshot: StateSnapshot) -> dict[str, Any]:
    return {
        "snapshot_id": str(index),
        **snapshot.to_dict(),
    }


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
    return {
        "process_id": process.definition_id,
        "name": process.name,
        "storage": process.storage,
        "flow_count": len(process.flows),
    }


def process_detail(process: ProcessDefinition) -> dict[str, Any]:
    return process.to_dict()
