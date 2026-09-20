"""Rehydrate wait interests from instance / state snapshots (0.55.6).

Wait interests live under ``palm.wait.interests`` on job/instance state.
Normalize after restore so corrupt rows never block resume.

Pure ``palm.core.wait`` home — callers above core must not reach through
``palm.system`` for this (0.71.19 cut the common→system edge).
"""

from __future__ import annotations

from typing import Any

from palm.core.wait.interest import STATE_KEY_WAIT_INTERESTS, WaitInterest
from palm.core.wait.state_ops import list_wait_interests, open_wait_interest


def rehydrate_wait_interests(state: Any) -> list[WaitInterest]:
    """Normalize open wait interests on restored state.

    Re-writes the list from successfully parsed interests (drops corrupt rows).
    Returns the rehydrated interests.
    """
    interests = list_wait_interests(state)
    # Force a clean write so partial/corrupt snapshot rows are pruned.
    setter = getattr(state, "set", None)
    if callable(setter):
        setter(STATE_KEY_WAIT_INTERESTS, [w.to_dict() for w in interests])
    return interests


def rehydrate_wait_interests_from_snapshot(
    snapshot: dict[str, Any],
    state: Any,
) -> list[WaitInterest]:
    """Copy wait interests from a raw snapshot dict onto ``state`` (if present)."""
    raw = snapshot.get(STATE_KEY_WAIT_INTERESTS)
    if not isinstance(raw, list):
        return rehydrate_wait_interests(state)
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            interest = WaitInterest.from_dict(item)
        except (TypeError, ValueError):
            continue
        open_wait_interest(state, interest, replace_same_target=True)
    return rehydrate_wait_interests(state)


__all__ = [
    "rehydrate_wait_interests",
    "rehydrate_wait_interests_from_snapshot",
]
