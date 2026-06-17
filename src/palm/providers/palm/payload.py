"""Job payload helpers for Palm compositional invocations."""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import Job


def job_payload(job: Job) -> dict[str, Any]:
    """Serialize a local orchestration job for provider results."""
    return {
        "job_id": job.id,
        "instance_id": job.metadata.get("instance_id"),
        "status": job.status.value,
        "result": job.result,
        "metadata": dict(job.metadata),
        "error": str(job.error) if job.error else None,
    }


def remote_job_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize a remote job response into the local payload shape."""
    if "job_id" not in payload and payload.get("jobs"):
        first = payload["jobs"][0]
        if isinstance(first, dict):
            return remote_job_payload(first)
    return {
        "job_id": payload.get("job_id"),
        "instance_id": payload.get("instance_id"),
        "status": payload.get("status"),
        "result": payload.get("result"),
        "metadata": dict(payload.get("metadata") or {}),
        "error": payload.get("error"),
    }


def with_invoke_context(
    payload: dict[str, Any],
    *,
    depth: int,
    chain: tuple[str, ...],
    parent_job_id: str | None,
) -> dict[str, Any]:
    """Attach recursion/correlation fields to an invoke result payload."""
    enriched = dict(payload)
    enriched["invoke_depth"] = depth
    enriched["invoke_chain"] = list(chain)
    enriched["parent_job_id"] = parent_job_id
    return enriched
