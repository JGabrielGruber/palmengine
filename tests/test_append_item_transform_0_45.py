"""0.45.1 — append_item transform rule."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.common.transforms import autoload
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.engine import TransformEngine
from palm.core.transform.registry import transform_registry
from tests.core.fakes import TestState


@pytest.fixture(autouse=True)
def _rules() -> None:
    transform_registry.clear()
    autoload()


@pytest.fixture
def transform_engine() -> Iterator[TransformEngine]:
    engine = TransformEngine()
    engine.initialize()
    yield engine
    engine.shutdown()


def test_append_item_prepends_and_caps(transform_engine) -> None:
    state = TestState()
    state.set("events", [{"offset": 1}, {"offset": 2}])
    state.set("row", {"offset": 3, "type": "inbound.received"})

    transform_engine.apply_to_state(
        "append_item",
        state,
        "row",
        target_key="events",
        max_items=2,
    )
    events = state.get("events")
    assert len(events) == 2
    assert events[0]["offset"] == 3
    assert events[1]["offset"] == 1


def test_append_item_dedups_unique_field(transform_engine) -> None:
    state = TestState()
    state.set("events", [{"offset": 1}, {"offset": 2}])
    state.set("row", {"offset": 2, "type": "dup"})

    transform_engine.apply_to_state(
        "append_item",
        state,
        "row",
        target_key="events",
        unique_field="offset",
    )
    events = state.get("events")
    assert len(events) == 2
    assert events[0]["type"] == "dup"
    assert events[1]["offset"] == 1


def test_append_item_starts_empty_list(transform_engine) -> None:
    state = TestState()
    state.set("row", {"id": "a"})

    transform_engine.apply_to_state(
        "append_item",
        state,
        "row",
        target_key="events",
    )
    assert state.get("events") == [{"id": "a"}]


def test_append_item_requires_state(transform_engine) -> None:
    with pytest.raises(TransformApplicationError, match="requires blackboard state"):
        transform_engine.apply("append_item", {"id": 1})