"""Assistant shaping for design publish / proposal paths."""

from __future__ import annotations

from typing import Any


def design_proposal_id_from_path(path: list[str], result: dict[str, Any]) -> str | None:
    if len(path) >= 3 and path[0] == "design" and path[1] == "proposals":
        return path[2]
    proposal_id = result.get("proposal_id")
    return str(proposal_id) if proposal_id else None


def shape_design_publish_assistant(result: dict[str, Any]) -> dict[str, Any]:
    """Human-first envelope for publish_flow / publish_resource responses."""
    status = result.get("status")
    shaped: dict[str, Any] = {
        "status": status,
        "stage": result.get("stage"),
        "hint": result.get("hint"),
        "actions": result.get("actions") or [],
    }
    if result.get("proposal_id") is not None:
        shaped["proposal_id"] = result["proposal_id"]
    if result.get("flow_id") is not None:
        shaped["flow_id"] = result["flow_id"]
    if result.get("revision") is not None:
        shaped["revision"] = result["revision"]
    if result.get("resource_ref") is not None:
        shaped["resource_ref"] = result["resource_ref"]
    if status == "committed":
        shaped["question"] = (
            f"Published {result.get('flow_id') or result.get('resource_ref')!r}. "
            "Use actions to run or inspect."
        )
    elif status == "blocked":
        shaped["question"] = "Publish blocked by validation — fix body and retry."
        if result.get("validation") is not None:
            shaped["validation"] = result["validation"]
    else:
        shaped["result"] = result
    return shaped


__all__ = [
    "design_proposal_id_from_path",
    "shape_design_publish_assistant",
]
