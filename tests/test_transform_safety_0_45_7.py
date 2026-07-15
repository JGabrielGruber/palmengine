"""0.45.7 — put_resource list persist defaults + TransformLeaf batch safety."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest

from examples.definitions.system.event_watch import PALM_SYSTEM_WATCH_EVENT_FLOW
from palm.common.patterns import build_pattern
from palm.common.patterns.build_context import PatternBuildContext
from palm.common.transforms import autoload
from palm.common.transforms.builder import build_transform_leaf, transform_step_from_mapping
from palm.common.transforms.rules.put_resource import PutResourceRule
from palm.core import PatternStatus
from palm.core.behavior_tree import TransformLeaf
from palm.core.resource.result import ProviderResult
from palm.core.transform.base import TransformMode
from palm.core.transform.engine import TransformEngine
from palm.core.transform.registry import transform_registry
from tests.core.fakes import TestState


@pytest.fixture
def transform_engine() -> Iterator[TransformEngine]:
    transform_registry.clear()
    autoload()
    engine = TransformEngine()
    engine.initialize()
    yield engine
    engine.shutdown()
    transform_registry.clear()


def test_put_resource_declares_batch_mode() -> None:
    assert PutResourceRule.mode is TransformMode.BATCH


def test_transform_leaf_put_resource_list_without_batch_override(transform_engine) -> None:
    engine = MagicMock()
    engine.invoke.return_value = ProviderResult.ok(
        {"stored": True},
        action="put",
        resource_id="log/key",
    )
    state = TestState()
    state.set("events", [{"job_id": "a"}, {"job_id": "b"}])

    leaf = TransformLeaf(
        "persist_log",
        engine=transform_engine,
        source_key="events",
        rule="put_resource",
        options={"resource": "palm-system-event-log"},
        resource_engine=engine,
    )
    assert leaf.tick(state) == PatternStatus.SUCCESS
    engine.invoke.assert_called_once()
    assert engine.invoke.call_args.kwargs["params"]["value"] == [
        {"job_id": "a"},
        {"job_id": "b"},
    ]


def test_builder_leaf_put_resource_list_persists_whole(transform_engine) -> None:
    engine = MagicMock()
    engine.invoke.return_value = ProviderResult.ok(
        {},
        action="put",
        resource_id="log/key",
    )
    state = TestState()
    state.set("events", [{"id": "1"}, {"id": "2"}])

    spec = transform_step_from_mapping(
        {
            "name": "persist_log",
            "source_key": "events",
            "rule": "put_resource",
            "options": {"resource": "my-log", "action": "put"},
        }
    )
    leaf = build_transform_leaf(
        spec,
        engine=transform_engine,
        resource_engine=engine,
    )
    assert leaf.tick(state) == PatternStatus.SUCCESS
    assert engine.invoke.call_args.kwargs["params"]["value"] == [{"id": "1"}, {"id": "2"}]


def test_event_watch_pipeline_persist_step_has_no_batch_override() -> None:
    steps = (PALM_SYSTEM_WATCH_EVENT_FLOW.options or {}).get("steps") or []
    persist = next(s for s in steps if s.get("name") == "persist_log")
    assert persist.get("rule") == "put_resource"
    assert "batch" not in persist


def test_event_watch_pipeline_tick_persists_list() -> None:
    """Real flow slice: append_item + put_resource without batch:false."""
    transform_registry.clear()
    autoload()

    resource_engine = MagicMock()
    stored: list[object] = []

    def _invoke(*_a, **kwargs):
        if kwargs.get("action") == "get":
            return ProviderResult.ok({"value": list(stored) or []}, action="get")
        if kwargs.get("action") == "put":
            val = (kwargs.get("params") or {}).get("value")
            stored.clear()
            if isinstance(val, list):
                stored.extend(val)
            elif val is not None:
                stored.append(val)
            return ProviderResult.ok({"value": val}, action="put")
        return ProviderResult.ok({}, action="get")

    resource_engine.invoke.side_effect = _invoke

    ctx = PatternBuildContext(resource_engine=resource_engine)
    pattern = build_pattern(PALM_SYSTEM_WATCH_EVENT_FLOW, context=ctx)

    state = TestState()
    state.set("probe", {"load": True})
    state.set("event", {"job_id": "job-1", "flow": "quick"})
    state.set("etype", "job.completed")
    state.set("event_id", "evt-1")

    assert pattern.tick(state) == PatternStatus.SUCCESS
    assert len(stored) == 1
    assert stored[0].get("job_id") == "job-1"