"""Tests for ContextEngine."""

from __future__ import annotations

import pytest

from palm.core import ContextEngine, ContextError


def test_root_context_by_default() -> None:
    engine = ContextEngine()
    assert engine.depth == 1
    assert engine.current_name == "root"


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


def test_initialize_with_seed() -> None:
    engine = ContextEngine()
    engine.initialize(initial={"tenant": "acme"})
    assert engine.get("tenant") == "acme"


def test_frames_snapshot() -> None:
    engine = ContextEngine()
    engine.push("a")
    engine.push("b")
    frames = engine.frames()
    assert len(frames) == 3
    assert frames[-1]["_name"] == "b"


def test_shutdown_resets_stack() -> None:
    engine = ContextEngine()
    engine.initialize()
    engine.push("temp")
    engine.shutdown()
    assert engine.depth == 1
    assert engine.current_name == "root"