"""Flow step explanation — metadata for operator debugging."""

from __future__ import annotations

from typing import Any


def explain_flow_step(flow: dict[str, Any], step_slug: str) -> dict[str, Any] | None:
    """Return step metadata from a verbose flow definition dict."""
    options = flow.get("options")
    if not isinstance(options, dict):
        return None

    steps = options.get("steps")
    if not isinstance(steps, list):
        return None

    for step in steps:
        if not isinstance(step, dict):
            continue
        slug = step.get("slug")
        if slug is None:
            continue
        if str(slug) == step_slug:
            return _step_payload(step, flow_name=flow.get("name"), pattern=flow.get("pattern"))
    return None


def _step_payload(step: dict[str, Any], *, flow_name: Any, pattern: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "flow": flow_name,
        "pattern": pattern,
        "slug": step.get("slug"),
        "title": step.get("title"),
        "prompt": step.get("prompt"),
        "field_type": step.get("field_type"),
        "step_kind": step.get("step_kind"),
        "choices": step.get("choices"),
        "required": step.get("required"),
        "resource_ref": step.get("resource_ref"),
        "transform_rule": step.get("transform_rule") or step.get("rule"),
        "commit_hook": step.get("commit_hook"),
        "min_items": step.get("min_items"),
        "item_fields": step.get("item_fields"),
    }
    return {key: value for key, value in payload.items() if value is not None}


__all__ = ["explain_flow_step"]
