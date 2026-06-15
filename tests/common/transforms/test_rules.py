"""Tests for built-in common transform rules."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from palm.common.transforms import (
    INSTALLED_TRANSFORMS,
    TransformExecutor,
    autoload,
    transform_rule,
)
from palm.core import DictStateSchema, StateValidationError, TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext
from palm.core.transform.registry import transform_registry
from tests.core.fakes import TestState


@pytest.fixture
def executor() -> TransformExecutor:
    transform_registry.clear()
    autoload()
    return TransformExecutor()


def test_installed_transforms_register(executor: TransformExecutor) -> None:
    expected = set(INSTALLED_TRANSFORMS)
    assert set(INSTALLED_TRANSFORMS) == expected
    for name in INSTALLED_TRANSFORMS:
        transform_registry.get(name)
    engine = executor.engine
    assert engine.is_initialized


def test_rename_field_rule(executor: TransformExecutor) -> None:
    result = executor.apply(
        "rename_field",
        {"first_name": "Ada", "role": "admin"},
        from_key="first_name",
        to_key="name",
    )
    assert result.value == {"name": "Ada", "role": "admin"}


def test_map_fields_keep_unmapped(executor: TransformExecutor) -> None:
    result = executor.apply(
        "map_fields",
        {"first_name": "Ada", "last_name": "Lovelace", "id": 1},
        mapping={"first_name": "name", "last_name": "surname"},
        keep_unmapped=True,
    )
    assert result.value == {"name": "Ada", "surname": "Lovelace", "id": 1}


def test_map_fields_strict(executor: TransformExecutor) -> None:
    result = executor.apply(
        "map_fields",
        {"first_name": "Ada", "noise": True},
        mapping={"first_name": "name"},
        keep_unmapped=False,
    )
    assert result.value == {"name": "Ada"}


def test_filter_items_by_equals(executor: TransformExecutor) -> None:
    items = [
        {"id": "a", "active": True},
        {"id": "b", "active": False},
        {"id": "c", "active": True},
    ]
    result = executor.apply("filter_items", items, field="active", equals=True)
    assert result.value == [{"id": "a", "active": True}, {"id": "c", "active": True}]


def test_filter_items_truthy(executor: TransformExecutor) -> None:
    items = [
        {"id": "a", "tags": ["x"]},
        {"id": "b", "tags": []},
        {"id": "c", "tags": None},
    ]
    result = executor.apply("filter_items", items, field="tags", is_truthy=True)
    assert result.value == [{"id": "a", "tags": ["x"]}]


def test_callable_single(executor: TransformExecutor) -> None:
    result = executor.apply("callable", 3, fn=lambda value: value + 1)
    assert result.value == 4


def test_callable_per_item_list(executor: TransformExecutor) -> None:
    result = executor.apply("callable", [1, 2, 3], fn=lambda value: value * 2)
    assert result.value == [2, 4, 6]


def test_string_format_template_and_case(executor: TransformExecutor) -> None:
    result = executor.apply(
        "string_format",
        "ada",
        template="Hello, {value}!",
        case="upper",
    )
    assert result.value == "HELLO, ADA!"


def test_string_format_date(executor: TransformExecutor) -> None:
    result = executor.apply("string_format", "2026-01-05", date_format="%Y-%m-%d")
    assert result.value == "2026-01-05"


def test_callable_requires_fn(executor: TransformExecutor) -> None:
    with pytest.raises(TransformApplicationError, match="requires a callable"):
        executor.apply("callable", 1)


def test_apply_chain(executor: TransformExecutor) -> None:
    result = executor.apply_chain(
        ["map_fields", "rename_field"],
        {"first_name": "Ada", "id": 7, "noise": True},
        options_by_rule={
            "map_fields": {"mapping": {"first_name": "given_name"}, "keep_unmapped": False},
            "rename_field": {"from_key": "given_name", "to_key": "name"},
        },
    )
    assert result.value == {"name": "Ada"}


def test_apply_to_state_root(executor: TransformExecutor, test_state: TestState) -> None:
    test_state.set("user", {"first_name": "Ada"})
    result = executor.apply_to_state(
        "rename_field",
        test_state,
        "user",
        from_key="first_name",
        to_key="name",
    )
    assert result is not None
    assert test_state.get("user") == {"name": "Ada"}


def test_apply_to_state_scoped_with_schema(executor: TransformExecutor) -> None:
    schema = DictStateSchema(
        {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "minimum": 0},
            },
        },
    )
    state = TestState(schema=schema)
    state.bind_scope_schema("step", schema)
    with state.scope("step"):
        state.set_scoped("count", 2)
        executor.apply_to_state(
            "callable",
            state,
            "count",
            scoped=True,
            fn=lambda value: value + 1,
        )
        assert state.get_scoped("count") == 3

        state.set_scoped("count", -1)
        with pytest.raises(StateValidationError):
            executor.apply_to_state(
                "callable",
                state,
                "count",
                scoped=True,
                fn=lambda value: value,
            )


def test_apply_batch_to_state_filter(executor: TransformExecutor, test_state: TestState) -> None:
    test_state.set(
        "items",
        [
            {"id": "a", "active": True},
            {"id": "b", "active": False},
        ],
    )
    result = executor.apply_batch_to_state(
        "filter_items",
        test_state,
        "items",
        field="active",
        equals=True,
        per_item=False,
    )
    assert result is not None
    assert test_state.get("items") == [{"id": "a", "active": True}]


def test_pattern_can_register_custom_rule(executor: TransformExecutor) -> None:
    @transform_rule
    class UppercaseRule(BaseTransformRule):
        name: ClassVar[str] = "uppercase"

        def apply(self, context: TransformContext, **options: Any) -> TransformContext:
            value = context.value
            if isinstance(value, str):
                return context.advance(self.rule_name, value.upper())
            return context.advance(self.rule_name, value)

    result = executor.apply("uppercase", "ada")
    assert result.value == "ADA"
    assert "uppercase" in transform_registry.names()
