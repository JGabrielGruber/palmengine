"""Assist dispatch param helpers (shared by façade and profiles)."""

from __future__ import annotations

from typing import Any

# Params that must not leak into flows.run_wizard() body (dispatch/meta only).
_WIZARD_BODY_STRIP = frozenset(
    {
        "body",
        "value",
        "input",
        "format",
        "alias",
        "path",
        "session_id",
        "instance_id",
        "flow_id",
        "scenario_id",
        "include_input_schema",
        "auto_start",
        "auto_continue_intro",
        "profile",
        "collection_action",
        "edit",
        "query",
        "q",
        "limit",
        "kind",
    }
)


def want_input_schema(params: dict[str, Any] | None) -> bool:
    """True when Portal/WS asks for structured ``input`` widgets (0.32.6)."""
    if not params:
        return False
    raw = params.get("include_input_schema")
    if raw is True or raw == 1:
        return True
    if isinstance(raw, str) and raw.strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return False


def wizard_start_body(params: dict[str, Any]) -> dict[str, Any]:
    """Build run_wizard body without assist/dispatch meta keys (e.g. greeting ``value``)."""
    nested = params.get("body")
    if isinstance(nested, dict) and nested:
        source = nested
    else:
        source = params
    return {k: v for k, v in source.items() if k not in _WIZARD_BODY_STRIP}


__all__ = ["want_input_schema", "wizard_start_body"]
