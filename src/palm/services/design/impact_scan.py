"""Scan catalog flows for ``resource_ref`` usage — resource proposal impact."""

from __future__ import annotations

from typing import Any


def flows_referencing_resource(
    flows: list[Any],
    resource_ref: str,
) -> list[dict[str, str]]:
    """Return flow/step rows that reference ``resource_ref`` in wizard or pipeline steps."""
    hits: list[dict[str, str]] = []
    target = str(resource_ref).strip()
    if not target:
        return hits

    for flow in flows:
        flow_id = str(getattr(flow, "name", None) or getattr(flow, "id", None) or "")
        options = getattr(flow, "options", None) or {}
        if not isinstance(options, dict):
            continue
        steps = options.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            if str(step.get("resource_ref") or "") != target:
                continue
            hits.append(
                {
                    "flow_id": flow_id,
                    "step_slug": str(step.get("slug") or ""),
                    "step_kind": str(step.get("step_kind") or "input"),
                }
            )
    return hits


__all__ = ["flows_referencing_resource"]