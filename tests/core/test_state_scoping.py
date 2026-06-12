"""Tests for BaseState nested scoping."""

from __future__ import annotations

from typing import Any

import pytest

from palm.core import (
    NESTED_SCOPES_KEY,
    SCOPES_ROOT_KEY,
    BaseState,
    ContextError,
)
from palm.states import BlackboardState, DictBackedState
from tests.core.fakes import TestState


def test_dict_backed_state_exposes_scope_storage() -> None:
    state = DictBackedState()
    assert state.scope_storage() is state._data


def test_base_state_scoped_get_set() -> None:
    state = TestState()
    state.enter_scope("job")
    state.set_scoped("step", 1)
    assert state.get_scoped("step") == 1
    assert state.current_scope() == "job"
    assert state.get("step") is None

    state.enter_scope("tick")
    state.set_scoped("step", 2)
    assert state.get_scoped("step") == 2

    state.exit_scope()
    assert state.get_scoped("step") == 1

    state.exit_scope()
    assert state.get_scoped("step") is None


def test_base_state_set_scoped_requires_active_scope() -> None:
    state = TestState()
    with pytest.raises(ContextError, match="without an active scope"):
        state.set_scoped("step", 1)


def test_base_state_exit_scope_on_empty_stack() -> None:
    state = TestState()
    with pytest.raises(ContextError, match="stack is empty"):
        state.exit_scope()


def test_base_state_scope_context_manager() -> None:
    state = TestState()
    with state.scope("job") as scoped:
        assert scoped is state
        scoped.set_scoped("step", 1)
        assert scoped.get_scoped("step") == 1
    assert state.current_scope() is None


def test_nested_scoping_storage_layout() -> None:
    state = TestState()
    with state.scope("job"):
        state.set_scoped("step", 1)
        with state.scope("tick"):
            state.set_scoped("step", 2)

    scopes = state.get(SCOPES_ROOT_KEY)
    assert scopes == {
        "job": {
            "step": 1,
            NESTED_SCOPES_KEY: {"tick": {"step": 2}},
        },
    }


def test_blackboard_state_nested_scopes() -> None:
    state = BlackboardState()
    with state.scope("wizard"):
        state.set_scoped("answer", "yes")
        assert state.get_scoped("answer") == "yes"
    assert state.get_scoped("answer") is None
    assert state.snapshot()[SCOPES_ROOT_KEY] == {"wizard": {"answer": "yes"}}


def test_scoped_operations_require_scope_storage() -> None:
    class PlainState(BaseState):
        def __init__(self) -> None:
            super().__init__()
            self._data: dict[str, object] = {}

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

    state = PlainState()
    state.enter_scope("job")
    with pytest.raises(ContextError, match="nested scope storage"):
        state.set_scoped("flag", True)