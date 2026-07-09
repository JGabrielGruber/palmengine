"""Assistant shaping for flow create envelopes."""

from __future__ import annotations

from typing import Any

from palm.runtimes.mcp.flows.views import submission_view


def human_status(raw: object | None) -> str:
    if raw is None:
        return "waiting"
    text = str(raw).upper()
    if text == "WAITING_FOR_INPUT":
        return "waiting"
    if text in {"SUCCEEDED", "SUCCESS"}:
        return "complete"
    if text in {"FAILED", "CANCELLED"}:
        return "failed"
    if text == "RUNNING":
        return "running"
    return str(raw).lower()


def shape_flow_create_assistant(
    result: dict[str, Any],
    *,
    path: list[str],
) -> dict[str, Any]:
    """Minimal create envelope when first-turn re-inspect is unavailable."""
    session_id = result.get("session_id") or result.get("instance_id")
    flow_id = result.get("flow_id") or result.get("flow")
    if flow_id is None and len(path) >= 2 and path[0] == "flows":
        flow_id = path[1]
    shaped = submission_view(result)
    shaped["status"] = human_status(shaped.get("status"))
    shaped["question"] = (
        f"Session started for {flow_id!r}. Reply with your next answer via palm_assist."
    )
    shaped["hint"] = (
        f'palm_assist(params={{"session_id": "{session_id}", "flow_id": "{flow_id}", "value": "…"}})'
    )
    if session_id and flow_id:
        shaped["actions"] = [
            {
                "label": "Continue session",
                "alias": "flows/session-input",
                "params": {"session_id": session_id, "flow_id": flow_id},
            },
            {
                "label": "Inspect session",
                "alias": "flows/session",
                "params": {
                    "session_id": session_id,
                    "flow_id": flow_id,
                    "format": "assistant",
                },
            },
        ]
    return shaped


__all__ = ["human_status", "shape_flow_create_assistant"]
