"""Tests for ContextEngine."""

from __future__ import annotations

import pytest

from palm.core import (
    STATE_FRAME_KEY,
    ContextEngine,
    ContextError,
    DictStateSchema,
    StateNotConfiguredError,
)
from tests.core.fakes import TestState

SCHEMA = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "tenant": {"type": "string", "default": "default-tenant"},
        },
    },
)


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


def test_bind_and_push_state(test_state: TestState) -> None:
    test_state.set("tenant", "acme")
    engine = ContextEngine()
    engine.bind_state(test_state)
    assert engine.current_state is test_state
    assert engine.current_state.get("tenant") == "acme"

    scoped = TestState({"x": 1})
    engine.push("scoped", state=scoped)
    assert engine.current_state is scoped
    assert engine.current[STATE_FRAME_KEY] is scoped
    engine.pop()
    assert engine.current_state is test_state


def test_initialize_with_state() -> None:
    seeded = TestState({"seed": True})
    engine = ContextEngine()
    engine.initialize(state=seeded)
    assert engine.current_state is seeded
    assert engine.current_state.get("seed") is True


def test_initialize_with_schema() -> None:
    state = TestState()
    engine = ContextEngine()
    engine.initialize(state=state, schema=SCHEMA)
    assert engine.current_state is state
    assert state.schema is SCHEMA


def test_bind_schema_on_current_state() -> None:
    state = TestState()
    engine = ContextEngine()
    engine.initialize(state=state)
    engine.bind_schema(SCHEMA)
    state.apply_defaults()
    assert state.get("tenant") == "default-tenant"


def test_state_scope_context_manager() -> None:
    state = TestState()
    engine = ContextEngine()
    engine.initialize(state=state)

    with engine.state_scope("job") as scoped_state:
        assert scoped_state is state
        scoped_state.set_scoped("step", 1)
        assert engine.current_state_scope == "job"
        assert state.get_scoped("step") == 1

    assert engine.current_state_scope is None
    assert state.get_scoped("step") is None


def test_push_with_state_scope() -> None:
    state = TestState()
    engine = ContextEngine()
    engine.initialize(state=state)

    engine.push("session", state_scope=True)
    state.set_scoped("token", "abc")
    assert engine.state_scope_depth == 1
    assert engine.current_state_scope == "session"

    engine.pop()
    assert engine.state_scope_depth == 0
    assert state.get_scoped("token") is None


def test_push_state_scope_requires_bound_state() -> None:
    engine = ContextEngine()
    with pytest.raises(StateNotConfiguredError):
        engine.push("session", state_scope=True)


def test_scope_with_state_scope_flag() -> None:
    state = TestState()
    engine = ContextEngine()
    engine.initialize(state=state)

    with engine.scope("wizard", state_scope=True):
        state.set_scoped("answers", {"ok": True})
        assert state.get_scoped("answers") == {"ok": True}

    assert state.scope_depth() == 0