"""Mutation guard envelope — read vs drive signals for operator views."""

from __future__ import annotations

from typing import Any

_TERMINAL = frozenset({"SUCCEEDED", "SUCCESS", "FAILED", "CANCELLED"})


def build_mutation_envelope(inspect: dict[str, Any]) -> dict[str, Any]:
    """Build a mutation guard block for operator inspect views."""
    status = str(inspect.get("status") or "").upper()
    step = inspect.get("step") or inspect.get("current_step_slug")
    step_kind = inspect.get("step_kind")
    field_type = inspect.get("field_type")
    waiting = status == "WAITING_FOR_INPUT"

    mutations_allowed = waiting and status not in _TERMINAL
    confirm_step = step_kind == "summary" or field_type == "confirm"

    payload: dict[str, Any] = {
        "mutations_allowed": mutations_allowed,
        "requires_user_input": mutations_allowed,
        "step_slug": step,
    }
    if confirm_step:
        payload["confirm_step"] = True
        payload["agent_hint"] = (
            "Confirm step: do not send yes/no unless the user explicitly said yes or no."
        )
    elif not mutations_allowed:
        payload["agent_hint"] = (
            "Read-only: use palm_flows_session or MCP resources; do not send value/input."
        )
    return {key: value for key, value in payload.items() if value is not None}


__all__ = ["build_mutation_envelope"]