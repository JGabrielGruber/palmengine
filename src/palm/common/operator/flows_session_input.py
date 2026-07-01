"""Resolve flows session input params — shared by service dispatch and MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.common.operator.collection_drive import COLLECTION_ADD_ONE_SHOT, drive_collection_add
from palm.common.operator.input_coercion import resolve_mcp_wizard_input


def flatten_session_read_model(ctx: Any) -> dict[str, Any]:
    """Merge session context ``detail`` for wizard input coercion."""
    if hasattr(ctx, "to_dict"):
        payload = ctx.to_dict()
    elif isinstance(ctx, dict):
        payload = dict(ctx)
    else:
        return {"value": ctx}

    detail = payload.get("detail")
    if isinstance(detail, dict):
        merged = {**detail, **{k: v for k, v in payload.items() if k != "detail"}}
    else:
        merged = dict(payload)

    session_id = merged.get("session_id")
    if session_id is not None and merged.get("instance_id") is None:
        merged["instance_id"] = session_id
    return merged


def prepare_flows_session_input_params(params: dict[str, Any]) -> dict[str, Any]:
    """Normalize weak-LLM params before flows session input dispatch."""
    prepared = dict(params)
    collection_action = prepared.get("collection_action")
    if collection_action is not None and "input" not in prepared:
        prepared["input"] = str(collection_action)
    return prepared


def apply_flows_session_input(
    get_context: Callable[[], Any],
    provide_input: Callable[[Any], Any],
    params: dict[str, Any],
) -> Any:
    """Resolve params, apply one-shot collection drives, return final session context."""
    prepared = prepare_flows_session_input_params(params)
    inspect = flatten_session_read_model(get_context())
    resolved = resolve_mcp_wizard_input(
        input=prepared.get("input"),
        value=prepared.get("value"),
        wizard_view=inspect,
    )
    if (
        isinstance(resolved, tuple)
        and len(resolved) == 2
        and resolved[0] == COLLECTION_ADD_ONE_SHOT
    ):
        last_ctx: Any = None

        def provide(field_value: Any) -> dict[str, Any]:
            nonlocal last_ctx
            last_ctx = provide_input(field_value)
            return flatten_session_read_model(last_ctx)

        drive_collection_add(
            provide,
            value=resolved[1],
            wizard_view=inspect,
        )
        assert last_ctx is not None
        return last_ctx

    return provide_input(resolved)


__all__ = [
    "apply_flows_session_input",
    "flatten_session_read_model",
    "prepare_flows_session_input_params",
]