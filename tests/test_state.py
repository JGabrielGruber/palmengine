"""Tests for pluggable state implementations."""

from __future__ import annotations

from palm.core.context import BaseState
from palm.states import BlackboardState, TestState


def test_blackboard_state_crud() -> None:
    state = BlackboardState({"a": 1})
    assert state.get("a") == 1
    state.set("b", 2)
    assert state.has("b")
    state.delete("b")
    assert state.get("b") is None
    assert state.keys() == ["a"]
    snap = state.snapshot()
    state.clear()
    assert state.keys() == []
    assert snap == {"a": 1}


def test_recording_state_records_operations() -> None:
    state = TestState(record=True)
    state.set("x", 10)
    state.get("x")
    assert ("set", "x", 10) in state.operations
    assert ("get", "x", None) in state.operations


def test_blackboard_state_is_base_state() -> None:
    assert isinstance(BlackboardState(), BaseState)
