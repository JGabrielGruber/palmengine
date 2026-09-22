"""Wizard catalog helpers — step metadata for definition surfaces."""

from __future__ import annotations

from palm.definitions.flow import FlowDefinition


def flow_step_slugs(flow: FlowDefinition) -> list[str]:
    """Extract wizard step slugs from flow options when present."""
    options = flow.options or {}
    steps = options.get("steps")
    if not isinstance(steps, list):
        return []
    slugs: list[str] = []
    for step in steps:
        if isinstance(step, dict):
            slugs.extend(_collect_step_slugs(step))
    return slugs


def _collect_step_slugs(step: dict[str, object]) -> list[str]:
    collected: list[str] = []
    slug = step.get("slug")
    if slug:
        collected.append(str(slug))
    if str(step.get("step_kind") or "") == "branch":
        for label in ("then", "else"):
            nested = step.get(label)
            if isinstance(nested, list):
                for item in nested:
                    if isinstance(item, dict):
                        collected.extend(_collect_step_slugs(item))
    return collected


__all__ = ["flow_step_slugs"]