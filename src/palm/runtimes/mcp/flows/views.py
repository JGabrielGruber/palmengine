"""Flow session view helpers for MCP operator tools."""

from __future__ import annotations

from typing import Any

from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.view_registry import (
    OperatorViewContext,
    build_operator_view,
    normalize_view_format,
)
from palm.runtimes.server.surfaces.rest.responses import flatten_session_context, session_context_body


def flatten_session_view(ctx: Any) -> dict[str, Any]:
    """Flatten :class:`SessionContext` for compact wizard inspect."""
    return flatten_session_context(ctx)


def submission_view(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize create-session payloads for MCP consumers."""
    session_id = result.get("session_id")
    payload = dict(result)
    if session_id is not None:
        payload["instance_id"] = session_id
    return payload


def resolve_flow_id_from_inspect(view: dict[str, Any]) -> str | None:
    """Infer flow id from a pattern-aware inspect view."""
    metadata = view.get("metadata")
    if isinstance(metadata, dict):
        for key in ("flow", "flow_name", "wizard"):
            value = metadata.get(key)
            if value is not None:
                return str(value)
    for key in ("flow", "flow_name"):
        value = view.get(key)
        if value is not None:
            return str(value)
    flow_id = view.get("flow_id")
    return str(flow_id) if flow_id is not None else None


def ensure_flow_id(
    *,
    flow_id: str | None,
    session_id: str,
    inspect: dict[str, Any],
) -> str:
    """Return ``flow_id`` or resolve it from an inspect view."""
    if flow_id:
        return flow_id
    resolved = resolve_flow_id_from_inspect(inspect)
    if resolved:
        return resolved
    raise ValueError(
        f"flow_id is required for session {session_id!r} (could not infer from inspect)"
    )


def session_context_dict(ctx: Any) -> dict[str, Any]:
    return session_context_body(ctx)


def shape_flow_session_view(
    flat: dict[str, Any],
    *,
    format: str = "powertool",
    session_id: str | None = None,
    flow_id: str | None = None,
    path: list[str] | None = None,
    invoke_tree: dict[str, Any] | None = None,
    include: list[str] | None = None,
    truncate_answers_at: int = 2000,
) -> dict[str, Any]:
    """Shape a flattened flow session inspect view for operator consumers."""
    fmt = normalize_view_format(format or "powertool")
    if fmt == "verbose":
        return dict(flat)
    if fmt == "assistant":
        sid = session_id or flat.get("instance_id") or flat.get("session_id")
        fid = flow_id or flat.get("flow_name") or flat.get("flow")
        context = OperatorViewContext(
            session_id=str(sid) if sid is not None else None,
            flow_id=str(fid) if fid is not None else None,
            scenario_id=None,
            invoke_tree=invoke_tree,
            path=list(path or []),
        )
        return build_operator_view("assistant", flat_view=flat, context=context)
    return compact_wizard_inspect(
        flat,
        format="compact",
        include=include,
        truncate_answers_at=truncate_answers_at,
    )


__all__ = [
    "ensure_flow_id",
    "flatten_session_view",
    "resolve_flow_id_from_inspect",
    "session_context_dict",
    "shape_flow_session_view",
    "submission_view",
]