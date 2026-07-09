"""Flatten inspect payloads and merge snapshot fields into compose status."""

from __future__ import annotations

from typing import Any


def flatten_view(view: dict[str, Any] | Any) -> dict[str, Any]:
    if hasattr(view, "to_dict"):
        payload = view.to_dict()
    elif isinstance(view, dict):
        payload = dict(view)
    else:
        return {"value": view}

    detail = payload.get("detail")
    if isinstance(detail, dict):
        merged = {**detail, **{k: v for k, v in payload.items() if k != "detail"}}
    else:
        merged = dict(payload)

    session_id = merged.get("session_id")
    if session_id is not None and merged.get("instance_id") is None:
        merged["instance_id"] = session_id
    return merged


def merge_snapshot_fields(composed: dict[str, Any], snapshot: dict[str, Any]) -> None:
    for key in (
        "prompt",
        "prompt_title",
        "field_type",
        "step_kind",
        "collection_phase",
        "choices",
        "validation_error",
        "operator_mode",
        "resource_error",
        "resource_remediation",
        "required",
        "validation_rules",
        "item_fields",
        "collection_key",
        "min_items",
        "label_field",
        "resource_ref",
        "step_index",
        "slug",
        "step",
    ):
        if snapshot.get(key) is not None and composed.get(key) is None:
            composed[key] = snapshot[key]


def invoke_tree_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    session_id = snapshot.get("instance_id")
    tree: dict[str, Any] = {"instance_id": session_id}
    if snapshot.get("waiting_for_child"):
        child = snapshot.get("child")
        if isinstance(child, dict):
            tree["active_child"] = dict(child)
    return tree


__all__ = ["flatten_view", "invoke_tree_from_snapshot", "merge_snapshot_fields"]
