"""0.37 — drain + resource.changed enqueue (system work plane)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.work import WorkIntent
from services.execution.providers.service import ProviderExecutionService
from palm.system.subsystems.planes.work.plane import WorkPlaneService


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def _plane(
    storage: StorageEngine,
    submit_flow: Callable[[str, dict[str, Any]], Any],
    *,
    event: EventEngine | None = None,
    able: Callable[[], bool] | None = None,
    max_depth: int = 8,
    batch_size: int = 10,
    poll_interval: float = 1.0,
) -> WorkPlaneService:
    plane = WorkPlaneService()
    plane.attach(
        storage=storage,
        submit_flow=submit_flow,
        able=able if able is not None else (lambda: True),
        event=event,
        max_depth=max_depth,
        batch_size=batch_size,
        poll_interval=poll_interval,
        attach_events=event is not None,
    )
    return plane


def test_drain_runs_submit() -> None:
    storage = _storage()
    submitted: list[str] = []

    def submit(flow_id: str, payload: dict) -> None:
        submitted.append(flow_id)

    drain = _plane(storage, submit)
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
    drain = _plane(
        storage,
        lambda f, p: submitted.append(f),
        event=engine,
    )
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

        @property
        def execution(self):
            return self

        def invoke_resource(self, resource_ref=None, **kwargs):
            return self.resource.invoke(resource_ref, **kwargs)

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
