"""Tests for palm.common.transforms."""

from __future__ import annotations

from datetime import date

import pytest

from palm.common.transforms import (
    TransformPipeline,
    apply_pipeline,
    register_common_transforms,
    registered_common_transforms,
)
from palm.common.transforms.registry import clear_common_transforms
from palm.core.registry import transform_registry
from palm.core.transform import TransformEngine


@pytest.fixture
def transform_engine() -> TransformEngine:
    transform_registry.clear()
    clear_common_transforms()
    engine = TransformEngine()
    engine.initialize()
    register_common_transforms()
    yield engine
    engine.shutdown()
    transform_registry.clear()
    clear_common_transforms()


def test_register_common_transforms() -> None:
    transform_registry.clear()
    clear_common_transforms()
    register_common_transforms()
    names = registered_common_transforms()
    assert "rename" in names
    assert "calculate" in names
    assert "filter_list" in names


def test_rename_and_drop_fields(transform_engine: TransformEngine) -> None:
    pipeline = TransformPipeline.parse(
        {
            "chain": [
                {"rule": "rename", "from_key": "first_name", "to_key": "name"},
                {"rule": "drop_fields", "fields": ["noise"]},
            ]
        }
    )
    ctx = apply_pipeline(
        pipeline,
        {"first_name": "Ada", "noise": True},
        engine=transform_engine,
    )
    assert ctx.value == {"name": "Ada"}
    assert ctx.lens("rename") == {"name": "Ada", "noise": True}


def test_string_transforms(transform_engine: TransformEngine) -> None:
    upper = apply_pipeline(
        TransformPipeline.parse({"rule": "uppercase"}),
        "hello",
        engine=transform_engine,
    )
    assert upper.value == "HELLO"

    formatted = apply_pipeline(
        TransformPipeline.parse({"rule": "format_string", "template": "Hi {value}!"}),
        "Ada",
        engine=transform_engine,
    )
    assert formatted.value == "Hi Ada!"

    dated = apply_pipeline(
        TransformPipeline.parse({"rule": "format_date", "fmt": "%Y/%m/%d"}),
        date(2026, 6, 10),
        engine=transform_engine,
    )
    assert dated.value == "2026/06/10"


def test_filter_and_map_list(transform_engine: TransformEngine) -> None:
    rows = [
        {"id": "a", "label": "Alpha", "active": True},
        {"id": "b", "label": "Beta", "active": False},
        {"id": "c", "label": "Gamma", "active": True},
    ]
    pipeline = TransformPipeline.parse(
        {
            "chain": [
                {"rule": "filter_list", "field": "active", "equals": True},
                {
                    "rule": "map_list",
                    "sub_rule": "pick_fields",
                    "sub_options": {"fields": ["id", "label"]},
                },
            ]
        }
    )
    ctx = apply_pipeline(pipeline, rows, engine=transform_engine)
    assert ctx.value == [
        {"id": "a", "label": "Alpha"},
        {"id": "c", "label": "Gamma"},
    ]


def test_calculate_transform(transform_engine: TransformEngine) -> None:
    pipeline = TransformPipeline.parse(
        {
            "rule": "calculate",
            "expression": "quantity * price",
            "field": "total",
        }
    )
    ctx = apply_pipeline(
        pipeline,
        {"quantity": 3, "price": 10},
        engine=transform_engine,
    )
    assert ctx.value["total"] == 30