"""
Waiting job list helpers — enrich REST rows and slim MCP operator views.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.core.orchestration.exceptions import JobNotFoundError


def enrich_job_list_rows(runtime: Any, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve ``instance_id``, pattern, flow, and step for job list consumers."""
    lookup = _summaries_by_job_id(runtime)
    return [_enrich_job_list_row(runtime, row, lookup) for row in rows]


def slim_waiting_job_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Compact waiting-job row for MCP — never aliases ``job_id`` as ``instance_id``."""
    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    job_id = row.get("job_id")
    instance_id = row.get("instance_id") or metadata.get("instance_id")
    if instance_id is not None and str(instance_id) == str(job_id):
        instance_id = None

    pattern = row.get("pattern") or metadata.get("pattern")
    flow = row.get("flow") or metadata.get("flow_name") or metadata.get("flow")
    step = row.get("step") or metadata.get("step") or metadata.get("wizard_step_slug")

    payload: dict[str, Any] = {
        "job_id": job_id,
        "status": row.get("status"),
    }
    if instance_id:
        payload["instance_id"] = str(instance_id)
    if pattern is not None:
        payload["pattern"] = pattern
    if flow is not None:
        payload["flow"] = flow
    if step is not None:
        payload["step"] = step
    return payload


def _summaries_by_job_id(runtime: Any) -> dict[str, Any]:
    lookup: dict[str, Any] = {}
    manager = getattr(runtime, "instance_manager", None)
    if manager is None:
        return lookup
    try:
        summaries = manager.list_summaries()
    except Exception:
        return lookup
    for summary in summaries:
        job_id = getattr(summary, "job_id", None)
        if job_id:
            lookup[str(job_id)] = summary
    return lookup


def _enrich_job_list_row(
    runtime: Any,
    row: Mapping[str, Any],
    lookup: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(row)
    job_id = str(payload.get("job_id") or "")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    summary = lookup.get(job_id)
    instance_id = payload.get("instance_id") or metadata.get("instance_id")
    if not instance_id and summary is not None:
        instance_id = getattr(summary, "instance_id", None)

    if not metadata.get("pattern") and job_id:
        metadata = _live_job_metadata(runtime, job_id) or metadata

    if instance_id:
        payload["instance_id"] = str(instance_id)
    elif payload.get("instance_id") == job_id:
        payload.pop("instance_id", None)

    payload["metadata"] = metadata

    pattern = metadata.get("pattern")
    if pattern is not None:
        payload["pattern"] = pattern

    flow = metadata.get("flow_name") or metadata.get("flow")
    if not flow and summary is not None:
        flow = getattr(summary, "flow_name", None)
    if flow is not None:
        payload["flow"] = flow

    step = metadata.get("step") or metadata.get("wizard_step_slug")
    if not step and summary is not None:
        step = getattr(summary, "current_step_slug", None)
    if step is not None:
        payload["step"] = step

    return payload


def _live_job_metadata(runtime: Any, job_id: str) -> dict[str, Any] | None:
    get_job = getattr(runtime, "get_job", None)
    if get_job is None:
        return None
    try:
        job = get_job(job_id)
    except JobNotFoundError:
        return None
    except Exception:
        return None
    meta = job.metadata
    return dict(meta) if isinstance(meta, dict) else None


__all__ = ["enrich_job_list_rows", "slim_waiting_job_row"]