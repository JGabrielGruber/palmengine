"""Assistant ``actions`` for wizard collection steps — thin mapper, no pattern imports."""

from __future__ import annotations

from typing import Any


def build_collection_assistant_actions(
    composed: dict[str, Any],
    *,
    session_id: str,
    flow_id: str | None = None,
) -> list[dict[str, Any]]:
    """Build progressive-disclosure actions for collection menu phases."""
    if composed.get("collection_phase") != "menu":
        return []
    if not flow_id:
        return []

    input_path = ["flows", flow_id, "session", session_id, "input"]
    return [
        {
            "label": "Add item",
            "path": list(input_path),
            "params": {"input": "add"},
        },
        {
            "label": "Add titled item",
            "path": list(input_path),
            "params": {"input": "add", "value": "…"},
        },
    ]


__all__ = ["build_collection_assistant_actions"]