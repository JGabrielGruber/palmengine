"""
TestState — in-memory state with optional operation recording for assertions.
"""

from __future__ import annotations

from typing import Any, Literal

from palm.core.context import BaseState

StateOp = tuple[Literal["get", "set", "delete", "clear"], str, Any]


class RecordingState(BaseState):
    """Dict-backed state that records mutations for unit tests."""

    __test__ = False  # not a pytest test class

    def __init__(
        self,
        initial: dict[str, Any] | None = None,
        *,
        record: bool = True,
    ) -> None:
        self._data: dict[str, Any] = dict(initial) if initial else {}
        self._record = record
        self.operations: list[StateOp] = []

    def get(self, key: str, default: Any = None) -> Any:
        if self._record:
            self.operations.append(("get", key, default))
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if self._record:
            self.operations.append(("set", key, value))
        self._data[key] = value

    def has(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> None:
        if self._record:
            self.operations.append(("delete", key, None))
        self._data.pop(key, None)

    def clear(self) -> None:
        if self._record:
            self.operations.append(("clear", "", None))
        self._data.clear()

    def snapshot(self) -> dict[str, Any]:
        return dict(self._data)

    def keys(self) -> list[str]:
        return list(self._data.keys())