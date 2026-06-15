"""Tests for the pipeline pattern and transform flow definitions."""

from __future__ import annotations

import importlib

import pytest

from palm.common.patterns import PatternBuildContext, build_pattern
from palm.common.transforms import autoload
from palm.core.behavior_tree import PatternStatus
from palm.core.transform.registry import transform_registry
from palm.definitions import FlowDefinition
from tests.core.fakes import TestState


@pytest.fixture(autouse=True)
def _load_transforms() -> None:
    transform_registry.clear()
    autoload()


def test_pipeline_pattern_from_flow_definition() -> None:
    importlib.import_module("palm.patterns.pipeline")

    flow = FlowDefinition(
        id="flow-test-pipeline",
        name="test-pipeline",
        pattern="pipeline",
        options={
            "initial_state": {"payload": {"first_name": "Ada"}},
            "steps": [
                {
                    "name": "rename",
                    "source_key": "payload",
                    "target_key": "user",
                    "rule": "rename_field",
                    "options": {"from_key": "first_name", "to_key": "name"},
                },
            ],
        },
    )
    pattern = build_pattern(flow, context=PatternBuildContext())
    state = TestState()
    assert pattern.tick(state) == PatternStatus.SUCCESS
    assert state.get("user") == {"name": "Ada"}


def test_transform_demo_flow_shape() -> None:
    from examples.definitions.transform_demo import TRANSFORM_DEMO_FLOW

    assert TRANSFORM_DEMO_FLOW.pattern == "pipeline"
    assert len(TRANSFORM_DEMO_FLOW.options["steps"]) == 2
