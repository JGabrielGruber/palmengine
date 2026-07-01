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
            slug = step.get("slug")
            if slug:
                slugs.append(str(slug))
    return slugs


__all__ = ["flow_step_slugs"]