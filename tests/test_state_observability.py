"""Tests for state observability filtering and event payloads."""

from __future__ import annotations

from palm.common.state import (
    STATE_SCHEMA_BOUND,
    STATE_SCOPE_ENTERED,
    STATE_VALUE_SET,
    StateObserverConfig,
    observe_state,
)
from palm.core import DictStateSchema
from palm.core.event import EventEngine
from tests.core.fakes import TestState


def test_default_observer_emits_scope_not_values() -> None:
    events: list[str] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda event: events.append(event.type))

    state = TestState()
    observe_state(state, engine)
    state.set("__wizard__.answers", {"a": 1})
    state.enter_scope("step")

    assert STATE_SCOPE_ENTERED in events
    assert STATE_VALUE_SET not in events


def test_observer_can_enable_value_events() -> None:
    events: list[str] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda event: events.append(event.type))

    state = TestState()
    observe_state(state, engine, config=StateObserverConfig(emit_value_events=True))
    state.set("user_input", "hello")

    assert STATE_VALUE_SET in events


def test_observer_ignores_internal_key_prefixes() -> None:
    payloads: list[dict] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda event: payloads.append(dict(event.payload)))

    state = TestState()
    observe_state(
        state,
        engine,
        config=StateObserverConfig(emit_value_events=True),
    )
    state.set("__wizard__.answers", {"x": 1})
    state.set("business_key", "value")

    value_events = [payload for payload in payloads if payload.get("key")]
    assert len(value_events) == 1
    assert value_events[0]["key"] == "business_key"


def test_schema_bound_event_summarizes_scope_schema() -> None:
    payloads: list[dict] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe(STATE_SCHEMA_BOUND, lambda event: payloads.append(dict(event.payload)))

    state = TestState()
    observe_state(state, engine)
    state.bind_scope_schema("age", DictStateSchema({"type": "integer"}))

    assert payloads
    assert payloads[0]["scope"] == "age"
    assert payloads[0]["schema_type"] == "integer"
    assert "schema" not in payloads[0]


def test_restore_scope_stack_does_not_emit_observer_events() -> None:
    events: list[str] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda event: events.append(event.type))

    state = TestState()
    observe_state(state, engine)
    state.restore_scope_stack(["session", "step"])

    assert events == []
