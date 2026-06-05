"""Smoke tests for the restructured Palm package."""

from __future__ import annotations

import palm
from palm.core import BehaviorTreeEngine, pattern_registry, storage_registry
from palm.core.registry import Registry
from palm.patterns import wizard  # noqa: F401
from palm.storages import memory  # noqa: F401


def test_version() -> None:
    assert palm.__version__


def test_pattern_registry_has_wizard() -> None:
    assert "wizard" in pattern_registry.names()


def test_storage_registry_has_memory() -> None:
    assert "memory" in storage_registry.names()


def test_behavior_tree_engine_tick() -> None:
    engine = BehaviorTreeEngine()
    engine.initialize()
    cls = pattern_registry.get("wizard")
    engine.set_root(cls(name="test", steps=2))
    assert engine.tick().value == "running"
    assert engine.tick().value == "success"
    engine.shutdown()


def test_registry_unknown_raises() -> None:
    reg: Registry[object] = Registry("widget")
    try:
        reg.get("missing")
    except Exception as exc:
        assert "widget" in str(exc)
    else:
        raise AssertionError("expected RegistryError")