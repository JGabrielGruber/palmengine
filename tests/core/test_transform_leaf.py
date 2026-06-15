"""Tests for TransformLeaf behavior tree integration."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from palm.core import DictStateSchema, TransformApplicationError
from palm.core.behavior_tree import PatternStatus, RootNode, SequenceNode, TransformLeaf
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode
from palm.core.transform.engine import TransformEngine
from palm.core.transform.registry import transform_registry
from tests.core.fakes import TestState


class DoubleRule(BaseTransformRule):
    name: ClassVar[str] = "double"

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        return context.advance(self.rule_name, context.value * 2)


class RenameFieldRule(BaseTransformRule):
    name: ClassVar[str] = "rename_field"

    def __init__(self, *, from_key: str, to_key: str) -> None:
        super().__init__()
        self._from_key = from_key
        self._to_key = to_key

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, dict):
            raise TransformApplicationError("rename_field requires a mapping")
        out = dict(value)
        if self._from_key in out:
            out[self._to_key] = out.pop(self._from_key)
        return context.advance(self.rule_name, out)


class FilterItemsRule(BaseTransformRule):
    name: ClassVar[str] = "filter_items"
    mode: ClassVar[TransformMode] = TransformMode.BATCH

    def __init__(self, *, field: str, equals: Any) -> None:
        super().__init__()
        self._field = field
        self._equals = equals

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, list):
            raise TransformApplicationError("filter_items requires a list")
        out = [item for item in value if item.get(self._field) == self._equals]
        return context.advance(self.rule_name, out)


@pytest.fixture
def engine() -> TransformEngine:
    transform_registry.clear()
    transform_registry.register("double", DoubleRule)
    transform_registry.register("rename_field", RenameFieldRule)
    transform_registry.register("filter_items", FilterItemsRule)
    transform_engine = TransformEngine()
    transform_engine.initialize()
    yield transform_engine
    transform_engine.shutdown()
    transform_registry.clear()


def test_transform_leaf_single_rule(engine: TransformEngine, test_state: TestState) -> None:
    test_state.set("value", 3)
    leaf = TransformLeaf(
        "double_it",
        engine=engine,
        source_key="value",
        rule="double",
    )
    assert leaf.tick(test_state) == PatternStatus.SUCCESS
    assert test_state.get("value") == 6
    assert test_state.get(leaf.trace_key)["value"] == 6


def test_transform_leaf_chain(engine: TransformEngine, test_state: TestState) -> None:
    test_state.set("record", {"first_name": "Ada", "id": 1})
    leaf = TransformLeaf(
        "normalize",
        engine=engine,
        source_key="record",
        target_key="profile",
        chain=["rename_field"],
        options_by_rule={"rename_field": {"from_key": "first_name", "to_key": "name"}},
    )
    assert leaf.tick(test_state) == PatternStatus.SUCCESS
    assert test_state.get("profile") == {"name": "Ada", "id": 1}


def test_transform_leaf_batch_per_item(engine: TransformEngine, test_state: TestState) -> None:
    test_state.set(
        "rows",
        [{"first_name": "Ada"}, {"first_name": "Bob"}],
    )
    leaf = TransformLeaf(
        "map_rows",
        engine=engine,
        source_key="rows",
        rule="rename_field",
        batch=True,
        options={"from_key": "first_name", "to_key": "name"},
    )
    assert leaf.tick(test_state) == PatternStatus.SUCCESS
    assert test_state.get("rows") == [{"name": "Ada"}, {"name": "Bob"}]


def test_transform_leaf_scoped_write(engine: TransformEngine) -> None:
    state = TestState()
    with state.scope("step"):
        state.set_scoped("count", 2)
        leaf = TransformLeaf(
            "scoped_double",
            engine=engine,
            source_key="count",
            rule="double",
            scoped=True,
        )
        assert leaf.tick(state) == PatternStatus.SUCCESS
        assert state.get_scoped("count") == 4


def test_transform_leaf_schema_validation_failure(engine: TransformEngine) -> None:
    schema = DictStateSchema(
        {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "minimum": 0},
            },
        },
    )
    state = TestState(schema=schema)
    state.set("count", -5)
    leaf = TransformLeaf(
        "identity_double",
        engine=engine,
        source_key="count",
        rule="double",
        error_key="transform_error",
    )
    assert leaf.tick(state) == PatternStatus.FAILURE
    assert "transform_error" in state.keys()


def test_transform_leaf_skip_if_missing(engine: TransformEngine, test_state: TestState) -> None:
    leaf = TransformLeaf(
        "optional",
        engine=engine,
        source_key="missing",
        rule="double",
        skip_if_missing=True,
    )
    assert leaf.tick(test_state) == PatternStatus.SUCCESS


def test_transform_leaf_sequence_in_tree(engine: TransformEngine, test_state: TestState) -> None:
    test_state.set(
        "items",
        [
            {"first_name": "Ada", "active": True},
            {"first_name": "Bob", "active": False},
        ],
    )
    rename = TransformLeaf(
        "rename",
        engine=engine,
        source_key="items",
        target_key="renamed",
        rule="rename_field",
        batch=True,
        options={"from_key": "first_name", "to_key": "name"},
    )
    filter_leaf = TransformLeaf(
        "filter",
        engine=engine,
        source_key="renamed",
        target_key="active_items",
        rule="filter_items",
        options={"field": "active", "equals": True},
    )
    root = RootNode("root", child=SequenceNode("seq", children=[rename, filter_leaf]))
    assert root.tick(test_state) == PatternStatus.SUCCESS
    assert test_state.get("active_items") == [{"name": "Ada", "active": True}]
