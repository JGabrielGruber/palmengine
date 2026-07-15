"""0.45.2 — same-process inbound (mode=internal)."""

from __future__ import annotations

from palm.app import ApplicationHost, PalmSettings
from palm.app.host.inbound_service import InboundBindingService
from palm.common.resource.inbound import parse_inbound_spec
from palm.core.event import EventEngine
from palm.core.work import WorkIntent
from palm.definitions import FlowDefinition, ResourceDefinition


def test_parse_inbound_internal_mode() -> None:
    spec = parse_inbound_spec(
        {
            "inbound": {
                "enabled": True,
                "mode": "internal",
                "event_types": ["resource.changed", "inbound.received"],
                "work": {"flow_id": "on-internal-event"},
            }
        }
    )
    assert spec is not None
    assert spec.mode == "internal"
    assert spec.event_types == ("resource.changed", "inbound.received")


def test_internal_service_filters_event_types() -> None:
    enqueued: list[WorkIntent] = []
    events = EventEngine()
    events.initialize()

    svc = InboundBindingService(
        enqueue=lambda intent: enqueued.append(intent) or "id-1",
        event_engine=events,
        list_resources=lambda: [{"name": "watch", "provider": "palm"}],
        get_resource=lambda name: {
            "name": name,
            "provider": "palm",
            "params": {},
            "metadata": {
                "inbound": {
                    "enabled": True,
                    "mode": "internal",
                    "event_types": ["resource.changed"],
                    "work": {"flow_id": "react"},
                }
            },
        },
    )
    svc.reload_from_definitions()
    assert svc.start_workers() == 1

    events.emit("job.completed", job_id="j-1")
    assert enqueued == []

    events.emit("resource.changed", resource_ref="palm-todos", action="put")
    assert len(enqueued) == 1
    assert enqueued[0].target == "react"
    assert enqueued[0].payload["source"] == "internal"
    assert enqueued[0].payload["inbound"]["type"] == "resource.changed"

    svc.stop()
    events.shutdown()


def test_internal_inbound_on_host_without_loopback() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        repo = host.app.repository()
        repo.save_flow(
            FlowDefinition(
                name="internal-react",
                pattern="pipeline",
                options={
                    "steps": [
                        {
                            "name": "pick_action",
                            "source_key": "event",
                            "target_key": "action",
                            "rule": "jsonpath_extract",
                            "options": {"path": "action"},
                        }
                    ]
                },
            )
        )
        repo.save_resource(
            ResourceDefinition(
                name="palm-events-watch",
                provider="palm",
                action="get",
                resource_id="system/events",
                params={},
                metadata={
                    "inbound": {
                        "enabled": True,
                        "mode": "internal",
                        "event_types": ["resource.changed"],
                        "work": {
                            "flow_id": "internal-react",
                            "seed_state": {"event": "inbound.payload"},
                        },
                    }
                },
            )
        )
        host.reload_inbound_bindings()
        bindings = host.inbound.list_bindings()
        assert any(b.get("mode") == "internal" and b.get("status") == "listening" for b in bindings)

        host._app.runtime().event.emit(
            "resource.changed",
            resource_ref="palm-todos",
            action="put",
            provider="kv",
        )
        pending = host.work_drain.store.list_pending(limit=20)
        assert any(
            intent.target == "internal-react" and intent.payload.get("source") == "internal"
            for intent in pending
        )
        while host.work_drain.store.pending_count():
            host.work_drain.tick(limit=10)
        host._execution.flows.wait_until_idle(timeout=5.0)

        jobs = host.app.runtime().orchestration.list_jobs()
        target_job = next(
            (job for job in jobs if job.metadata.get("flow") == "internal-react"),
            None,
        )
        assert target_job is not None
        assert target_job.status.value == "SUCCEEDED"
        assert target_job.state.get("action") == "put"
        assert target_job.metadata.get("source") == "internal"
    finally:
        host.shutdown()