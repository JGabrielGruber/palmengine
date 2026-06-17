"""Resource observability — correlation metadata for ``resource.*`` events (core)."""

from __future__ import annotations

from typing import Any

EXECUTION_STATE_KEY = "__palm.execution"


def execution_block_from_state(state: Any) -> dict[str, Any]:
    """Read job/instance correlation stamped on blackboard state."""
    if state is None:
        return {}
    getter = getattr(state, "get", None)
    if not callable(getter):
        return {}
    raw = getter(EXECUTION_STATE_KEY)
    return dict(raw) if isinstance(raw, dict) else {}


def resource_correlation(
    state: Any | None = None,
    *,
    wizard: str | None = None,
    step_slug: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build correlation fields merged into ``resource.*`` event payloads."""
    correlation: dict[str, Any] = {}
    block = execution_block_from_state(state)
    for key in ("job_id", "instance_id", "trace_id", "flow", "wizard"):
        value = block.get(key)
        if value is not None:
            correlation[key] = value
    if wizard is not None:
        correlation["wizard"] = wizard
    if step_slug is not None:
        correlation["step_slug"] = step_slug
    if extra:
        correlation.update(extra)
    return correlation