"""Tests for StateSchema and BaseState validation."""

from __future__ import annotations

import pytest

from palm.core import DictStateSchema, StateValidationError
from tests.core.fakes import TestState

USER_SCHEMA = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "default": "anonymous"},
            "age": {"type": "integer", "minimum": 0},
            "role": {"type": "string", "enum": ["admin", "user"]},
        },
        "required": ["name"],
    },
)


def test_dict_schema_defaults() -> None:
    assert USER_SCHEMA.defaults() == {"name": "anonymous"}


def test_dict_schema_definition_property() -> None:
    assert USER_SCHEMA.definition["type"] == "object"


def test_dict_schema_validate_state_success() -> None:
    errors = USER_SCHEMA.validate_state({"name": "Ada", "age": 30, "role": "admin"})
    assert errors == []


def test_dict_schema_validate_state_missing_required() -> None:
    errors = USER_SCHEMA.validate_state({"age": 1})
    assert errors == ["missing required key: name"]


def test_dict_schema_validate_key_type_mismatch() -> None:
    with pytest.raises(StateValidationError, match="expected integer"):
        USER_SCHEMA.validate_key("age", "not-a-number")


def test_dict_schema_validate_key_enum() -> None:
    with pytest.raises(StateValidationError, match="not in enum"):
        USER_SCHEMA.validate_key("role", "guest")


def test_dict_schema_validate_value_scalar() -> None:
    age_schema = DictStateSchema({"type": "integer", "minimum": 18})
    assert age_schema.validate_value(25, path="age") == []
    errors = age_schema.validate_value(16, path="age")
    assert errors == ["age: 16 < minimum 18"]


def test_base_state_apply_defaults() -> None:
    state = TestState(schema=USER_SCHEMA)
    state.apply_defaults()
    assert state.get("name") == "anonymous"
    assert not state.has("age")


def test_base_state_set_validated_accepts_valid_value() -> None:
    state = TestState(schema=USER_SCHEMA)
    state.set_validated("name", "Ada")
    state.set_validated("age", 21)
    assert state.get("name") == "Ada"
    assert state.get("age") == 21


def test_base_state_set_validated_rejects_invalid_value() -> None:
    state = TestState(schema=USER_SCHEMA)
    with pytest.raises(StateValidationError):
        state.set_validated("age", -1)


def test_base_state_validate_returns_errors() -> None:
    state = TestState({"age": "bad"}, schema=USER_SCHEMA)
    errors = state.validate()
    assert "missing required key: name" in errors
    assert any("expected integer" in error for error in errors)


def test_base_state_validate_key_without_schema() -> None:
    state = TestState({"x": 1})
    assert state.validate() == []
    assert state.validate_key("x") == []


def test_dict_schema_validate_string_length_constraints() -> None:
    schema = DictStateSchema({"type": "string", "minLength": 2, "maxLength": 5})
    assert schema.validate_value("ab", path="name") == []
    assert schema.validate_value("abcde", path="name") == []
    assert schema.validate_value("a", path="name") == ["name: length 1 < minLength 2"]
    assert schema.validate_value("abcdef", path="name") == [
        "name: length 6 > maxLength 5",
    ]


def test_dict_schema_validate_array_item_count_constraints() -> None:
    schema = DictStateSchema(
        {
            "type": "array",
            "minItems": 1,
            "maxItems": 2,
            "items": {"type": "string"},
        },
    )
    assert schema.validate_value(["a"], path="tags") == []
    assert schema.validate_value([], path="tags") == ["tags: length 0 < minItems 1"]
    assert schema.validate_value(["a", "b", "c"], path="tags") == [
        "tags: length 3 > maxItems 2",
    ]


def test_dict_schema_validate_state_with_length_constraints() -> None:
    schema = DictStateSchema(
        {
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 3},
                "tags": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string"},
                },
            },
            "required": ["title"],
        },
    )
    errors = schema.validate_state({"title": "ab", "tags": []})
    assert "title: length 2 < minLength 3" in errors
    assert "tags: length 0 < minItems 1" in errors


def test_dict_schema_validate_union_type_accepts_null() -> None:
    schema = DictStateSchema({"type": ["string", "null"]})
    assert schema.validate_value(None, path="due_date") == []
    assert schema.validate_value("2026-06-12", path="due_date") == []
    errors = schema.validate_value(42, path="due_date")
    assert errors == ["due_date: expected ['string', 'null'], got int"]
