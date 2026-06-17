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
        "wizard_step_slug": snapshot.wizard_step_slug,
    }


def snapshot_detail(index: int, snapshot: StateSnapshot) -> dict[str, Any]:
    return {
        "snapshot_id": str(index),
        **snapshot.to_dict(),
    }


def flow_summary(flow: FlowDefinition) -> dict[str, Any]:
    return {
        "flow_id": flow.definition_id,
        "name": flow.name,
        "pattern": flow.pattern,
        "has_state_schema": flow.has_state_schema,
    }


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