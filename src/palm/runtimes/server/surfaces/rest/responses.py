"""REST response builders — consistent success envelopes."""

from __future__ import annotations

from typing import Any

from palm.common.runtimes.server.protocol import ServerResponse
from palm.core.orchestration import Job


def ok(body: dict[str, Any]) -> ServerResponse:
    return ServerResponse(status=200, body=body)


def created(body: dict[str, Any]) -> ServerResponse:
    return ServerResponse(status=201, body=body)


def accepted(body: dict[str, Any]) -> ServerResponse:
    return ServerResponse(status=202, body=body)


def job_snapshot(job: Job) -> dict[str, Any]:
    return {
        "job_id": job.id,
        "status": job.status.value,
        "metadata": job.metadata,
    }


def job_accepted(job: Job) -> ServerResponse:
    return accepted(job_snapshot(job))


def session_context_body(ctx: Any) -> dict[str, Any]:
    """Normalize a :class:`~palm.services.execution.flows.schemas.SessionContext` payload."""
    if hasattr(ctx, "to_dict"):
        return ctx.to_dict()
    if isinstance(ctx, dict):
        return ctx
    return {"value": ctx}


def flatten_session_context(ctx: Any) -> dict[str, Any]:
    """Merge ``SessionContext.detail`` for REST/MCP operator ergonomics."""
    payload = session_context_body(ctx)
    detail = payload.get("detail")
    if isinstance(detail, dict):
        merged = {**detail, **{k: v for k, v in payload.items() if k != "detail"}}
    else:
        merged = dict(payload)
    session_id = merged.get("session_id")
    if session_id is not None:
        merged["instance_id"] = session_id
    return merged


def read_model_body(row: Any) -> dict[str, Any]:
    if hasattr(row, "to_dict"):
        return row.to_dict()
    if isinstance(row, dict):
        return row
    return {"value": row}


def html(body: str, *, status: int = 200) -> ServerResponse:
    """Return an HTML response (e.g. interactive API docs)."""
    return ServerResponse(
        status=status,
        content_type="text/html; charset=utf-8",
        raw_body=body.encode("utf-8"),
    )
