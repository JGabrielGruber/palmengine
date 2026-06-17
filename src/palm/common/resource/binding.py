"""State promotion helpers for resource param binding."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.core.context import BaseState


def promote_binding_keys(state: BaseState, mapping: Mapping[str, Any]) -> None:
    """
    Copy ``mapping`` entries onto ``state`` when the key is unset.

    Used by wizard resource steps so prior answers are visible to
    ``{{ state.* }}`` placeholder binding.
    """
    for key, value in mapping.items():
        if value is None:
            continue
        if state.get(key) is None:
            state.set(key, value)