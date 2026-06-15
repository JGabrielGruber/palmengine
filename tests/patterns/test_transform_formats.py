"""Tests for the transform-formats pipeline example."""

from __future__ import annotations

from palm.common.patterns import build_pattern
from palm.common.transforms import autoload
from palm.core import PatternStatus
from palm.core.transform.registry import transform_registry
from examples.definitions.transform_formats import TRANSFORM_FORMATS_FLOW
from tests.core.fakes import TestState


def test_transform_formats_pipeline_exports_csv() -> None:
    transform_registry.clear()
    autoload()
    pattern = build_pattern(TRANSFORM_FORMATS_FLOW)
    state = TestState()
    state.set("raw_json", TRANSFORM_FORMATS_FLOW.options["initial_state"]["raw_json"])

    assert pattern.tick(state) == PatternStatus.SUCCESS

    csv_text = state.get("csv_export")
    assert isinstance(csv_text, str)
    lines = csv_text.strip().splitlines()
    assert lines[0] == "name,score"
    assert "Ada,98" in lines
    assert "Grace,95" in lines