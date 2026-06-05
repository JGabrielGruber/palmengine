"""Smoke tests for the restructured Palm package."""

from __future__ import annotations

import palm
from palm.core import BehaviorTreeEngine, pattern_registry, storage_registry
from palm.core.registry import Registry
from palm.patterns import wizard  # noqa: F401
from palm.storages import memory  # noqa: F401


def test_version() -> None:
    assert palm.__version__ == "0.5.0-dev"


def test_pattern_registry_has_wizard() -> None:
    assert "wizard" in pattern_registry.names()


def test_storage_registry_has_memory() -> None:
    assert "memory" in storage_registry.names()


def test_behavior_tree_engine_tick() -> None:
    from palm.states import BlackboardState

    engine = BehaviorTreeEngine()
    engine.initialize(state=BlackboardState())
    cls = pattern_registry.get("wizard")
    wiz = cls(name="test", steps=2)
    engine.set_root(wiz)
    assert engine.tick().value == "waiting_for_input"
    wiz.provide_input(engine.state, "a")
    assert engine.tick().value == "waiting_for_input"
    wiz.provide_input(engine.state, "b")
    assert engine.tick().value == "success"
    engine.shutdown()


def test_embedded_runtime_quick_wizard() -> None:
    from palm.runtimes.embedded import EmbeddedRuntime

    rt = EmbeddedRuntime()
    rt.start()
    try:
        job = rt.submit_wizard(steps=2)
        assert job.status.value == "WAITING_FOR_INPUT"
        rt.provide_input(job.id, "first")
        rt.provide_input(job.id, "second")
        assert job.status.value == "SUCCEEDED"
    finally:
        rt.stop()


def test_registry_unknown_raises() -> None:
    reg: Registry[object] = Registry("widget")
    try:
        reg.get("missing")
    except Exception as exc:
        assert "widget" in str(exc)
    else:
        raise AssertionError("expected RegistryError")
