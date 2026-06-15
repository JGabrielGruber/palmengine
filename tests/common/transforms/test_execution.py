"""Tests for transform execution helpers."""

from __future__ import annotations

from palm.common.transforms import (
    apply_transform,
    apply_transform_to_state,
    default_executor,
)
from palm.core.transform.registry import transform_registry
from tests.core.fakes import TestState


def test_default_executor_is_singleton() -> None:
    transform_registry.clear()
    first = default_executor()
    second = default_executor()
    assert first is second
    assert first.engine.is_initialized


def test_apply_transform_module_helper() -> None:
    transform_registry.clear()
    result = apply_transform(
        "rename_field",
        {"first_name": "Bob"},
        from_key="first_name",
        to_key="name",
    )
    assert result.value == {"name": "Bob"}


def test_apply_transform_to_state_module_helper(test_state: TestState) -> None:
    transform_registry.clear()
    test_state.set("payload", {"first_name": "Bob"})
    result = apply_transform_to_state(
        "rename_field",
        test_state,
        "payload",
        from_key="first_name",
        to_key="name",
    )
    assert result is not None
    assert test_state.get("payload") == {"name": "Bob"}
