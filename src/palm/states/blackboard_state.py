"""
Dict-backed blackboard state — default behavior-tree storage.
"""

from __future__ import annotations

from palm.states.dict_backed_state import DictBackedState


class BlackboardState(DictBackedState):
    """In-memory key-value state for behavior tree execution."""

    def __repr__(self) -> str:
        return f"BlackboardState(keys={len(self._data)})"