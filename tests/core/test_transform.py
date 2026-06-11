"""Tests for TransformEngine, primitives, and TransformContext."""

from __future__ import annotations

from datetime import date

import pytest

from palm.core import (
    TransformApplicationError,
    TransformContext,
    TransformEngine,
    transform_registry,
)
from palm.core.transform.primitives import register_core_transforms


@pytest.fixture
def transform_engine() -> TransformEngine:
    transform_registry.clear()
    engine = TransformEngine()
    engine.initialize()
    yield engine
    engine.shutdown()
    transform_registry.clear()


def test_transform_context_chain_and_lens() -> None:
    ctx = TransformContext(original={"id": 1, "label": "Ada"})
    ctx = ctx.advance("step_a", {"id": 1})
    ctx = ctx.advance("step_b", {"name": "Ada"})

    assert ctx.original == {"id": 1, "label": "Ada"}
    assert ctx.value == {"name": "Ada"}
    assert ctx.steps == ("step_a", "step_b")
    assert ctx.lens("step_a") == {"id": 1}
    assert ctx.lens("missing") is None


def test_rename_field_transform(transform_engine: TransformEngine) -> None:
    ctx = transform_engine.apply(
        "rename_field",
        {"first_name": "Ada", "role": "admin"},
        from_key="first_name",
        to_key="name",
    )
    assert ctx.value == {"name": "Ada", "role": "admin"}


def test_pick_fields_transform(transform_engine: TransformEngine) -> None:
    ctx = transform_engine.apply(
        "pick_fields",
        {"id": 1, "name": "Ada", "secret": "x"},
        fields=["id", "name"],
    )
    assert ctx.value == {"id": 1, "name": "Ada"}


def test_format_value_transform(transform_engine: TransformEngine) -> None:
    ctx = transform_engine.apply("format_value", "ada", template="Hello {value}")
    assert ctx.value == "Hello ada"

    ctx_date = transform_engine.apply(
        "format_value",
        date(2026, 6, 10),
        template="%Y-%m-%d",
    )
    assert ctx_date.value == "2026-06-10"


def test_filter_list_transform(transform_engine: TransformEngine) -> None:
    items = [
        {"id": "a", "active": True},
        {"id": "b", "active": False},
        {"id": "c", "active": True},
    ]
    ctx = transform_engine.apply_auto(
        "filter_list",
        items,
        field="active",
        equals=True,
    )
    assert ctx.value == [{"id": "a", "active": True}, {"id": "c", "active": True}]


def test_map_list_transform(transform_engine: TransformEngine) -> None:
    rows = [{"first_name": "Ada"}, {"first_name": "Bob"}]
    ctx = transform_engine.apply_auto(
        "map_list",
        rows,
        sub_rule="rename_field",
        sub_options={"from_key": "first_name", "to_key": "name"},
    )
    assert ctx.value == [{"name": "Ada"}, {"name": "Bob"}]


def test_apply_chain_preserves_original(transform_engine: TransformEngine) -> None:
    ctx = transform_engine.apply_chain(
        ["pick_fields", "rename_field"],
        {"id": 7, "first_name": "Ada", "noise": True},
        options_by_rule={
            "pick_fields": {"fields": ["id", "first_name"]},
            "rename_field": {"from_key": "first_name", "to_key": "name"},
        },
    )
    assert ctx.original == {"id": 7, "first_name": "Ada", "noise": True}
    assert ctx.value == {"id": 7, "name": "Ada"}
    assert ctx.lens("pick_fields") == {"id": 7, "first_name": "Ada"}


def test_apply_batch_per_item(transform_engine: TransformEngine) -> None:
    contexts = transform_engine.apply_batch(
        "rename_field",
        [{"first_name": "Ada"}, {"first_name": "Bob"}],
        from_key="first_name",
        to_key="name",
    )
    assert [ctx.value for ctx in contexts] == [{"name": "Ada"}, {"name": "Bob"}]


def test_unknown_transform_raises(transform_engine: TransformEngine) -> None:
    with pytest.raises(Exception, match="Unknown transform"):
        transform_engine.apply("not_registered", {"a": 1})


def test_register_core_transforms_idempotent() -> None:
    transform_registry.clear()
    register_core_transforms()
    names = transform_registry.names()
    register_core_transforms()
    assert transform_registry.names() == names
    assert "rename_field" in names