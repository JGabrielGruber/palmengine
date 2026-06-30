"""
Compositional session status — invoke stack plus compact wizard snapshot.
"""

from __future__ import annotations

from typing import Any

from palm.common.operator.result_summary import summarize_commit_result


def build_compose_status(
    invoke_tree: dict[str, Any],
    wizard_inspect: dict[str, Any],
) -> dict[str, Any]:
    """Summarize a compositional wizard session for operator agents."""
    payload: dict[str, Any] = {
        "instance_id": invoke_tree.get("instance_id") or wizard_inspect.get("instance_id"),
        "flow": wizard_inspect.get("flow"),
        "status": wizard_inspect.get("status"),
        "step": wizard_inspect.get("step"),
        "step_kind": wizard_inspect.get("step_kind"),
        "root": invoke_tree.get("root"),
        "focus": invoke_tree.get("focus"),
        "active_child": invoke_tree.get("active_child"),
        "ancestors": invoke_tree.get("ancestors"),
        "answers_keys": wizard_inspect.get("answers_keys"),
        "next_actions": wizard_inspect.get("next_actions"),
        "links": invoke_tree.get("links"),
    }

    preview = wizard_inspect.get("answers_preview")
    if isinstance(preview, dict) and preview:
        payload["answers_preview"] = preview

    if wizard_inspect.get("waiting_for_child"):
        payload["waiting_for_child"] = True
        child = wizard_inspect.get("child")
        if isinstance(child, dict):
            payload["child"] = child

    for key in (
        "collection_phase",
        "collection_field",
        "field_type",
        "choices",
        "validation_error",
        "operator_hint",
        "job_id",
        "committed",
        "result",
    ):
        value = wizard_inspect.get(key)
        if value is not None:
            payload[key] = value

    result = wizard_inspect.get("result")
    if result is not None:
        summary = summarize_commit_result(result)
        if summary:
            payload["result_summary"] = summary

    return {key: value for key, value in payload.items() if value is not None}


__all__ = ["build_compose_status"]
