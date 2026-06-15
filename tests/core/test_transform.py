"""Tests for TransformEngine, BaseTransformRule, and BaseState integration."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from palm.core import (
    DictStateSchema,
    RegistryError,
    StateValidationError,
    TransformApplicationError,
    TransformContext,
    TransformEngine,
    TransformMode,
    transform_registry,
)
from palm.core.transform.base import BaseTransformRule
from tests.core.fakes import TestState


class IdentityRule(BaseTransformRule):
    name: ClassVar[str] = "identity"

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        return context.advance(self.rule_name, context.value)


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


class PickFieldsRule(BaseTransformRule):
    name: ClassVar[str] = "pick_fields"

    def __init__(self, *, fields: list[str]) -> None:
        super().__init__()
        self._fields = list(fields)

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, dict):
            raise TransformApplicationError("pick_fields requires a mapping")
        out = {key: value[key] for key in self._fields if key in value}
        return context.advance(self.rule_name, out)


class FilterListRule(BaseTransformRule):
    name: ClassVar[str] = "filter_list"
    mode: ClassVar[TransformMode] = TransformMode.BATCH

    def __init__(self, *, field: str, equals: Any) -> None:
        super().__init__()
        self._field = field
        self._equals = equals

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, list):
            raise TransformApplicationError("filter_list requires a list")
        out = [item for item in value if item.get(self._field) == self._equals]
        return context.advance(self.rule_name, out)


class MapListRule(BaseTransformRule):
    name: ClassVar[str] = "map_list"
    mode: ClassVar[TransformMode] = TransformMode.AUTO

    def __init__(self, *, sub_rule: str, sub_options: dict[str, Any] | None = None) -> None:
        super().__init__()
        self._sub_rule = sub_rule
        self._sub_options = dict(sub_options or {})

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        engine = options.get("_engine")
        value = context.value
        if not isinstance(value, list) or engine is None:
            raise TransformApplicationError("map_list requires a list and engine")
        mapped = [engine.apply(self._sub_rule, item, **self._sub_options).value for item in value]
        return context.advance(self.rule_name, mapped)


def _register_test_rules() -> None:
    transform_registry.register("identity", IdentityRule)
    transform_registry.register("double", DoubleRule)
    transform_registry.register("rename_field", RenameFieldRule)
    transform_registry.register("pick_fields", PickFieldsRule)
    transform_registry.register("filter_list", FilterListRule)
    transform_registry.register("map_list", MapListRule)


@pytest.fixture
def transform_engine() -> TransformEngine:
    transform_registry.clear()
    _register_test_rules()
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


def test_transform_context_with_state(test_state: TestState) -> None:
    ctx = TransformContext(original=1).with_state(test_state)
    assert ctx.state is test_state
    assert ctx.value == 1


def test_identity_transform(transform_engine: TransformEngine) -> None:
    result = transform_engine.apply("identity", {"a": 1})
    assert result.value == {"a": 1}
    assert result.original == {"a": 1}


def test_rename_field_transform(transform_engine: TransformEngine) -> None:
    result = transform_engine.apply(
        "rename_field",
        {"first_name": "Ada", "role": "admin"},
        from_key="first_name",
        to_key="name",
    )
    assert result.value == {"name": "Ada", "role": "admin"}


def test_pick_fields_transform(transform_engine: TransformEngine) -> None:
    result = transform_engine.apply(
        "pick_fields",
        {"id": 1, "name": "Ada", "secret": "x"},
        fields=["id", "name"],
    )
    assert result.value == {"id": 1, "name": "Ada"}


def test_apply_chain_preserves_original(transform_engine: TransformEngine) -> None:
    result = transform_engine.apply_chain(
        ["pick_fields", "rename_field"],
        {"id": 7, "first_name": "Ada", "noise": True},
        options_by_rule={
            "pick_fields": {"fields": ["id", "first_name"]},
            "rename_field": {"from_key": "first_name", "to_key": "name"},
        },
    )
    assert result.original == {"id": 7, "first_name": "Ada", "noise": True}
    assert result.value == {"id": 7, "name": "Ada"}
    assert result.context.lens("pick_fields") == {"id": 7, "first_name": "Ada"}


def test_apply_batch_per_item(transform_engine: TransformEngine) -> None:
    results = transform_engine.apply_batch(
        "rename_field",
        [{"first_name": "Ada"}, {"first_name": "Bob"}],
        from_key="first_name",
        to_key="name",
    )
    assert [item.value for item in results] == [{"name": "Ada"}, {"name": "Bob"}]


def test_filter_list_auto_batch(transform_engine: TransformEngine) -> None:
    items = [
        {"id": "a", "active": True},
        {"id": "b", "active": False},
        {"id": "c", "active": True},
    ]
    result = transform_engine.apply_auto(
        "filter_list",
        items,
        field="active",
        equals=True,
    )
    assert result.value == [{"id": "a", "active": True}, {"id": "c", "active": True}]


def test_map_list_auto(transform_engine: TransformEngine) -> None:
    rows = [{"first_name": "Ada"}, {"first_name": "Bob"}]
    result = transform_engine.apply_auto(
        "map_list",
        rows,
        sub_rule="rename_field",
        sub_options={"from_key": "first_name", "to_key": "name"},
    )
    assert result.value == [{"name": "Ada"}, {"name": "Bob"}]


def test_unknown_transform_raises(transform_engine: TransformEngine) -> None:
    with pytest.raises(RegistryError, match="Unknown transform"):
        transform_engine.apply("not_registered", {"a": 1})


def test_unsupported_value_raises(transform_engine: TransformEngine) -> None:
    class StrictRule(BaseTransformRule):
        name: ClassVar[str] = "strict"

        def supports(self, value: Any) -> bool:
            return isinstance(value, dict)

        def apply(self, context: TransformContext, **options: Any) -> TransformContext:
            return context.advance(self.rule_name, context.value)

    transform_registry.register("strict", StrictRule)
    with pytest.raises(TransformApplicationError, match="does not support"):
        transform_engine.apply("strict", [1, 2, 3])


def test_apply_to_state_root_keys(transform_engine: TransformEngine, test_state: TestState) -> None:
    test_state.set("payload", {"first_name": "Ada"})
    result = transform_engine.apply_to_state(
        "rename_field",
        test_state,
        "payload",
        from_key="first_name",
        to_key="name",
    )
    assert result is not None
    assert test_state.get("payload") == {"name": "Ada"}
    assert result.state_writes == (("payload", {"name": "Ada"}),)


def test_apply_to_state_with_trace(
    transform_engine: TransformEngine, test_state: TestState
) -> None:
    test_state.set("value", 3)
    result = transform_engine.apply_to_state(
        "double",
        test_state,
        "value",
        trace_key="trace",
    )
    assert result is not None
    assert test_state.get("value") == 6
    trace = test_state.get("trace")
    assert trace["original"] == 3
    assert trace["value"] == 6
    assert trace["steps"] == ["double"]


def test_apply_to_state_skip_if_missing(
    transform_engine: TransformEngine,
    test_state: TestState,
) -> None:
    result = transform_engine.apply_to_state(
        "double",
        test_state,
        "missing",
        skip_if_missing=True,
    )
    assert result is None


def test_apply_to_state_raises_when_missing(
    transform_engine: TransformEngine,
    test_state: TestState,
) -> None:
    with pytest.raises(TransformApplicationError, match="missing or null"):
        transform_engine.apply_to_state("double", test_state, "missing")


def test_apply_chain_to_state(transform_engine: TransformEngine, test_state: TestState) -> None:
    test_state.set(
        "record",
        {"id": 7, "first_name": "Ada", "noise": True},
    )
    result = transform_engine.apply_chain_to_state(
        ["pick_fields", "rename_field"],
        test_state,
        "record",
        options_by_rule={
            "pick_fields": {"fields": ["id", "first_name"]},
            "rename_field": {"from_key": "first_name", "to_key": "name"},
        },
    )
    assert result is not None
    assert test_state.get("record") == {"id": 7, "name": "Ada"}


def test_apply_batch_to_state_per_item(
    transform_engine: TransformEngine,
    test_state: TestState,
) -> None:
    test_state.set("rows", [{"first_name": "Ada"}, {"first_name": "Bob"}])
    result = transform_engine.apply_batch_to_state(
        "rename_field",
        test_state,
        "rows",
        from_key="first_name",
        to_key="name",
    )
    assert result is not None
    assert test_state.get("rows") == [{"name": "Ada"}, {"name": "Bob"}]


def test_apply_batch_to_state_whole_list(
    transform_engine: TransformEngine,
    test_state: TestState,
) -> None:
    items = [
        {"id": "a", "active": True},
        {"id": "b", "active": False},
    ]
    test_state.set("items", items)
    result = transform_engine.apply_batch_to_state(
        "filter_list",
        test_state,
        "items",
        field="active",
        equals=True,
        per_item=False,
    )
    assert result is not None
    assert test_state.get("items") == [{"id": "a", "active": True}]


def test_scoped_state_reads_and_writes(
    transform_engine: TransformEngine,
    test_state: TestState,
) -> None:
    test_state.set("global", "root")
    with test_state.scope("step"):
        test_state.set_scoped("value", 4)
        result = transform_engine.apply_to_state(
            "double",
            test_state,
            "value",
            scoped=True,
        )
        assert result is not None
        assert test_state.get_scoped("value") == 8
        assert test_state.get("global") == "root"


def test_scoped_schema_validation_on_write(
    transform_engine: TransformEngine,
) -> None:
    schema = DictStateSchema(
        {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 18},
            },
        },
    )
    state = TestState(schema=schema)
    state.bind_scope_schema("step", schema)
    with state.scope("step"):
        state.set_scoped("age", 25)
        transform_engine.apply_to_state(
            "identity",
            state,
            "age",
            scoped=True,
            validate_output=True,
        )
        assert state.get_scoped("age") == 25

        state.set_scoped("age", 10)
        with pytest.raises(StateValidationError):
            transform_engine.apply_to_state(
                "identity",
                state,
                "age",
                scoped=True,
                validate_output=True,
            )


def test_effective_schema_used_for_root_write(
    transform_engine: TransformEngine,
) -> None:
    schema = DictStateSchema(
        {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "minimum": 0},
            },
        },
    )
    state = TestState(schema=schema)
    state.set("count", 5)
    transform_engine.apply_to_state("identity", state, "count")
    assert state.get("count") == 5

    state.set("count", -1)
    with pytest.raises(StateValidationError):
        transform_engine.apply_to_state("identity", state, "count")


def test_read_write_state_value_helpers(
    transform_engine: TransformEngine,
    test_state: TestState,
) -> None:
    test_state.set("x", 1)
    assert transform_engine.read_state_value(test_state, "x") == 1
    transform_engine.write_state_value(test_state, "x", 2, validate=False)
    assert test_state.get("x") == 2

    with test_state.scope("inner"):
        test_state.set_scoped("y", 3)
        assert transform_engine.read_state_value(test_state, "y", scoped=True) == 3
        transform_engine.write_state_value(test_state, "y", 4, scoped=True, validate=False)
        assert test_state.get_scoped("y") == 4


def test_transform_registry_thread_safe_register() -> None:
    transform_registry.clear()
    transform_registry.register("identity", IdentityRule)
    transform_registry.register("identity", IdentityRule)
    assert transform_registry.names() == ["identity"]
    transform_registry.clear()
