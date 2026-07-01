"""Flow session view helpers for MCP operator tools."""

from __future__ import annotations

from typing import Any

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


__all__ = [
    "ensure_flow_id",
    "flatten_session_view",
    "resolve_flow_id_from_inspect",
    "session_context_dict",
    "submission_view",
]