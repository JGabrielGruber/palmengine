"""Tests for the transform-shaping pipeline example."""

from __future__ import annotations

from examples.definitions.transform_shaping import TRANSFORM_SHAPING_FLOW
from palm.common.patterns import build_pattern
from palm.common.transforms import autoload
from palm.core import PatternStatus
from palm.core.transform.registry import transform_registry
from tests.core.fakes import TestState


def test_transform_shaping_pipeline() -> None:
    transform_registry.clear()
    autoload()
    pattern = build_pattern(TRANSFORM_SHAPING_FLOW)
    state = TestState()
    state.set("order", {"sku": "widget", "price": 25, "qty": 2})

    assert pattern.tick(state) == PatternStatus.SUCCESS
    assert state.get("total") == 50
    assert state.get("category") == "hardware"
    assert state.get("size_label") == "large"
