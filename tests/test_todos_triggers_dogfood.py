"""0.40.1 — todos pack declares on_resource triggers; put enqueues WorkIntent."""

from __future__ import annotations

from palm.app.host.work_drain_service import WorkDrainService
from palm.common.triggers import parse_triggers
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from examples.definitions.todos.analytics import TODO_ANALYTICS_FLOW


def test_todo_analytics_flow_declares_triggers() -> None:
    specs = parse_triggers(TODO_ANALYTICS_FLOW.options)
    kinds = {s.kind for s in specs}
    assert "on_resource" in kinds
    resources = {s.resource for s in specs if s.kind == "on_resource"}
    assert "put-palm-todos" in resources
    assert "palm-todos" in resources
    assert all(s.work_flow_id == "todo-analytics" for s in specs if s.kind == "on_resource")


def test_put_palm_todos_enqueues_todo_analytics() -> None:
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    submitted: list[str] = []
    engine = EventEngine()
    engine.initialize()
    drain = WorkDrainService(
        storage,
        submit_flow=lambda f, _p: submitted.append(f),
        event_engine=engine,
    )
    drain.attach_events(engine)
    drain.reload_triggers(
        [
            {
                "name": "todo-analytics",
                "metadata": TODO_ANALYTICS_FLOW.options,
            }
        ]
    )
    engine.emit("resource.changed", resource_ref="put-palm-todos", action="put")
    assert drain.store.pending_count() == 1
    n = drain.tick()
    assert n == 1
    assert submitted == ["todo-analytics"]
    engine.shutdown()
