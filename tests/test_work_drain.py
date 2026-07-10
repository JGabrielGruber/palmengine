"""0.37 — drain + resource.changed enqueue."""

from __future__ import annotations

from palm.app.host.work_drain_service import WorkDrainService
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.work import WorkIntent
from palm.services.execution.providers.service import ProviderExecutionService
from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.schemas import CqrsSchemaRegistry


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_drain_runs_submit() -> None:
    storage = _storage()
    submitted: list[str] = []

    def submit(flow_id: str, payload: dict) -> None:
        submitted.append(flow_id)

    drain = WorkDrainService(storage, submit_flow=submit, able=lambda: True)
    drain.enqueue(WorkIntent(kind="run_flow", target="my-flow"))
    n = drain.tick()
    assert n == 1
    assert submitted == ["my-flow"]
    assert drain.store.pending_count() == 0


def test_resource_changed_enqueues_trigger() -> None:
    storage = _storage()
    submitted: list[str] = []
    engine = EventEngine()
    engine.initialize()
    drain = WorkDrainService(
        storage, submit_flow=lambda f, p: submitted.append(f), event_engine=engine
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
                            "resource": "palm-todos",
                            "actions": ["put"],
                            "work": {"flow_id": "todo-analytics"},
                        }
                    ]
                },
            }
        ]
    )
    engine.emit("resource.changed", resource_ref="palm-todos", action="put")
    assert drain.store.pending_count() == 1
    drain.tick()
    assert submitted == ["todo-analytics"]
    engine.shutdown()


def test_provider_emit_resource_changed() -> None:
    engine = EventEngine()
    engine.initialize()
    seen: list[str] = []

    def handler(event) -> None:
        seen.append(event.type)

    engine.subscribe("resource.changed", handler)

    class _RT:
        class resource:
            is_initialized = True

            @staticmethod
            def initialize() -> None:
                return None

            @staticmethod
            def invoke(*a, **k):
                from palm.core.resource.result import ProviderResult

                return ProviderResult.ok(
                    {"x": 1}, metadata={"action": "put", "provider": "kv"}
                )

    svc = ProviderExecutionService(
        commands=CommandBus(),
        queries=QueryBus(),
        schemas=CqrsSchemaRegistry(),
        runtime=_RT(),  # type: ignore[arg-type]
        event_engine=engine,
    )
    body = svc.invoke("any-ref", action="put")
    assert body["success"] is True
    assert "resource.changed" in seen
    engine.shutdown()
