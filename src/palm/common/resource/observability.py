"""Resource observability helpers — stamp execution context from orchestration hooks."""

from __future__ import annotations

from typing import Any

from palm.core.resource.observability import EXECUTION_STATE_KEY, resource_correlation

__all__ = ["EXECUTION_STATE_KEY", "resource_correlation", "stamp_execution_context"]


def stamp_execution_context(
    state: Any,
    *,
    job_id: str,
    instance_id: str | None = None,
    flow: str | None = None,
    wizard: str | None = None,
    trace_id: str | None = None,
) -> None:
    """Write execution correlation onto blackboard state before pattern ticks."""
    setter = getattr(state, "set", None)
    if not callable(setter):
        return
    block: dict[str, Any] = {"job_id": job_id}
    if instance_id is not None:
        block["instance_id"] = instance_id
    if flow is not None:
        block["flow"] = flow
    if wizard is not None:
        block["wizard"] = wizard
    if trace_id is not None:
        block["trace_id"] = trace_id
    setter(EXECUTION_STATE_KEY, block)
