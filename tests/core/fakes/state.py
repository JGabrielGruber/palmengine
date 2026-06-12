"""
TestState — dict-backed :class:`~palm.core.context.BaseState` for core unit tests.

Drop-in test double for production :class:`~palm.states.BlackboardState` with
optional operation recording for assertions.
"""

from __future__ import annotations

from typing import Any, Literal

from palm.core.context import StateSchema
from palm.states.dict_backed_state import DictBackedState

StateOp = tuple[Literal["get", "set", "delete", "clear"], str, Any]


class TestState(DictBackedState):
    """In-memory state for isolated ``palm.core`` tests."""

    __test__ = False

    def __init__(
        self,
        initial: dict[str, Any] | None = None,
        *,
        schema: StateSchema | None = None,
        record: bool = False,
    ) -> None:
        super().__init__(initial, schema=schema)
        self._record = record
        self.operations: list[StateOp] = []

    def get(self, key: str, default: Any = None) -> Any:
        if self._record:
            self.operations.append(("get", key, default))
        return super().get(key, default)

    def set(self, key: str, value: Any) -> None:
        if self._record:
            self.operations.append(("set", key, value))
        super().set(key, value)

    def delete(self, key: str) -> None:
        if self._record:
            self.operations.append(("delete", key, None))
        super().delete(key)

    def clear(self) -> None:
        if self._record:
            self.operations.append(("clear", "", None))
        super().clear()