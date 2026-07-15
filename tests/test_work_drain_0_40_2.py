"""0.40.2 — continuous drain loop · debounce · depth storm guard."""

from __future__ import annotations

import time

from palm.app.host.workplane.work_drain_service import WorkDrainService
from palm.common.triggers import TriggerRegistry
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.work import WorkIntent


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_debounce_suppresses_storm() -> None:
    reg = TriggerRegistry()
    reg.reload_from_flow_rows(
        [
            {
                "name": "w",
                "metadata": {
                    "triggers": [
                        {
                            "kind": "on_resource",
                            "resource": "palm-todos",
                            "actions": ["put"],
                            "debounce": 10.0,
                            "work": {
                                "flow_id": "todo-analytics",
                                "coalesce_key": "deb:palm-todos",
                            },
                        }
                    ]
                },
            }
        ]
    )
    first = reg.on_event(
        "resource.changed",
        {"resource_ref": "palm-todos", "action": "put"},
        now_ts=100.0,
    )
    second = reg.on_event(
        "resource.changed",
        {"resource_ref": "palm-todos", "action": "put"},
        now_ts=105.0,
    )
    third = reg.on_event(
        "resource.changed",
        {"resource_ref": "palm-todos", "action": "put"},
        now_ts=111.0,
    )
    assert len(first) == 1
    assert second == []
    assert len(third) == 1


def test_depth_drop_above_max() -> None:
    storage = _storage()
    drain = WorkDrainService(
        storage,
        submit_flow=lambda *_a, **_k: None,
        max_depth=2,
    )
    assert drain.enqueue(WorkIntent(kind="run_flow", target="a", depth=2)) != ""
    assert drain.enqueue(WorkIntent(kind="run_flow", target="b", depth=3)) == ""
    assert drain.dropped_depth_count == 1
    assert drain.store.pending_count() == 1


def test_trigger_depth_increments() -> None:
    reg = TriggerRegistry()
    reg.reload_from_flow_rows(
        [
            {
                "name": "w",
                "metadata": {
                    "triggers": [
                        {
                            "kind": "on_resource",
                            "resource": "palm-todos",
                            "actions": ["put"],
                            "work": {"flow_id": "todo-analytics"},
                        }
                    ]
                },
            }
        ]
    )
    intents = reg.on_event(
        "resource.changed",
        {"resource_ref": "palm-todos", "action": "put", "depth": 2},
    )
    assert len(intents) == 1
    assert intents[0].depth == 3


def test_background_drain_runs_when_able() -> None:
    storage = _storage()
    submitted: list[str] = []
    drain = WorkDrainService(
        storage,
        submit_flow=lambda f, _p: submitted.append(f),
        able=lambda: True,
        poll_interval=0.05,
        batch_size=5,
    )
    drain.enqueue(WorkIntent(kind="run_flow", target="bg-flow"))
    drain.start_background()
    try:
        deadline = time.time() + 2.0
        while not submitted and time.time() < deadline:
            time.sleep(0.05)
        assert submitted == ["bg-flow"]
        assert drain.is_running
    finally:
        drain.stop_background()
    assert not drain.is_running


def test_resource_storm_coalesce_store() -> None:
    """Many resource.changed with same coalesce_key → one pending intent."""
    storage = _storage()
    engine = EventEngine()
    engine.initialize()
    drain = WorkDrainService(
        storage,
        submit_flow=lambda *_a, **_k: None,
        event_engine=engine,
    )
    drain.attach_events(engine)
    drain.reload_triggers(
        [
            {
                "name": "w",
                "metadata": {
                    "triggers": [
                        {
                            "kind": "on_resource",
                            "resource": "put-palm-todos",
                            "actions": ["put"],
                            "work": {
                                "flow_id": "todo-analytics",
                                "coalesce_key": "storm:todos",
                            },
                        }
                    ]
                },
            }
        ]
    )
    for _ in range(20):
        engine.emit("resource.changed", resource_ref="put-palm-todos", action="put")
    assert drain.store.pending_count() == 1
    engine.shutdown()
