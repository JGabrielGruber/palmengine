"""Compat re-export — wait rehydrate lives in ``palm.core.wait`` (0.71.19)."""

from __future__ import annotations

from palm.core.wait import (
    rehydrate_wait_interests,
    rehydrate_wait_interests_from_snapshot,
)

__all__ = [
    "rehydrate_wait_interests",
    "rehydrate_wait_interests_from_snapshot",
]
