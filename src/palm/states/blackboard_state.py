"""
Dict-backed blackboard state — default behavior-tree storage.
"""

from __future__ import annotations

from typing import Any

from palm.core.context import BaseState, StateSchema


class BlackboardState(BaseState):
    """In-memory key-value state for behavior tree execution."""

    def __init__(
        self,
        initial: dict[str, Any] | None = None,
        *,
        schema: StateSchema | None = None,
    ) -> None:
        super().__init__(schema=schema)
        self._data: dict[str, Any] = dict(initial) if initial else {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def has(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()

    def snapshot(self) -> dict[str, Any]:
        return dict(self._data)

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def __repr__(self) -> str:
        return f"BlackboardState(keys={len(self._data)})"
