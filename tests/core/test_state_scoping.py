"""Tests for BaseState scoping and storage modes."""

from __future__ import annotations

from typing import Any

import pytest

from palm.core import (
    NESTED_SCOPES_KEY,
    SCOPES_ROOT_KEY,
    BaseState,
    ContextError,
    ScopeStorageMode,
    legacy_storage_key,
)
from palm.states import BlackboardState, DictBackedState
from tests.core.fakes import TestState


def test_scope_storage_mode_nested_for_dict_backed_state() -> None:
    state = DictBackedState()
    assert state.uses_nested_scopes is True
    assert state.scope_storage() is state._data


def test_scope_storage_mode_legacy_for_test_state_without_schema() -> None:
    state = TestState()
    assert state.uses_nested_scopes is False


def test_base_state_scoped_get_set() -> None:
    state = TestState(nested_scopes=False)
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
    state = TestState(nested_scopes=True)
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


def test_blackboard_state_uses_nested_scopes() -> None:
    state = BlackboardState()
    with state.scope("wizard"):
        state.set_scoped("answer", "yes")
        assert state.get_scoped("answer") == "yes"
    assert state.get_scoped("answer") is None
    assert state.snapshot()[SCOPES_ROOT_KEY] == {"wizard": {"answer": "yes"}}


def test_legacy_flat_scope_keys_remain_readable() -> None:
    state = TestState(nested_scopes=True)
    state.enter_scope("job")
    state.set(legacy_storage_key("job", "step"), 9)
    assert state.get_scoped("step") == 9


def test_legacy_mode_without_schema_uses_flat_keys() -> None:
    state = TestState(nested_scopes=False)
    state.enter_scope("job")
    state.set_scoped("step", 3)
    assert state.get("__palm:scope:job:step") == 3
    assert SCOPES_ROOT_KEY not in state.snapshot()


def test_base_state_legacy_subclass_without_super_init() -> None:
    """Subclasses that skip ``super().__init__`` still get lazy extensions."""

    class LegacyState(BaseState):
        def __init__(self) -> None:
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

    state = LegacyState()
    state.enter_scope("legacy")
    state.set_scoped("flag", True)
    assert state.get_scoped("flag") is True


def test_scope_storage_mode_enum_values() -> None:
    assert ScopeStorageMode.NESTED.value == "nested"
    assert ScopeStorageMode.LEGACY.value == "legacy"