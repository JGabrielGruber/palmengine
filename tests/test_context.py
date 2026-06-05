"""Tests for ContextEngine."""

from __future__ import annotations

import pytest

from palm.core import STATE_FRAME_KEY, ContextEngine, ContextError
from palm.states import BlackboardState, TestState


def test_root_context_by_default() -> None:
    engine = ContextEngine()
    assert engine.depth == 1
    assert engine.current_name == "root"
    assert engine.current_state is None


def test_push_pop_stack() -> None:
    engine = ContextEngine()
    frame = engine.push("session", user_id=42)
    assert frame["user_id"] == 42
    assert engine.depth == 2
    assert engine.current_name == "session"
    popped = engine.pop()
    assert popped["user_id"] == 42
    assert engine.depth == 1


def test_scope_context_manager() -> None:
    engine = ContextEngine()
    with engine.scope("job", job_id="j-1") as frame:
        assert frame["job_id"] == "j-1"
        engine.set("step", 1)
        assert engine.get("step") == 1
    assert engine.current_name == "root"
    assert engine.get("step") is None


def test_cannot_pop_root() -> None:
    engine = ContextEngine()
    with pytest.raises(ContextError):
        engine.pop()


def test_bind_state_on_frame() -> None:
    engine = ContextEngine()
    bb = BlackboardState()
    bb.set("tenant", "acme")
    engine.bind_state(bb)
    assert engine.current_state is bb
    assert engine.current_state.get("tenant") == "acme"


def test_push_with_state() -> None:
    engine = ContextEngine()
    ts = TestState({"x": 1})
    engine.push("scoped", state=ts)
    assert engine.current_state is ts
    assert engine.current[STATE_FRAME_KEY] is ts
    engine.pop()
    assert engine.current_state is None


def test_initialize_with_state() -> None:
    engine = ContextEngine()
    engine.initialize(state=BlackboardState({"seed": True}))
    assert engine.current_state is not None
    assert engine.current_state.get("seed") is True


def test_shutdown_resets_stack() -> None:
    engine = ContextEngine()
    engine.initialize()
    engine.push("temp")
    engine.shutdown()
    assert engine.depth == 1
    assert engine.current_name == "root"
