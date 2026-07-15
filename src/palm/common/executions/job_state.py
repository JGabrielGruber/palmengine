"""Coerce submission bodies into orchestration blackboard state."""

from __future__ import annotations

from typing import Any

from palm.core.context import BaseState
from palm.states import BlackboardState


def coerce_job_state(state: Any) -> BaseState | None:
    """Return ``BlackboardState`` from a dict or pass through existing state."""
    if state is None:
        return None
    if isinstance(state, BaseState):
        return state
    if isinstance(state, dict):
        return BlackboardState(state)
    raise TypeError(f"job state must be dict or BaseState, got {type(state).__name__}")


__all__ = ["coerce_job_state"]