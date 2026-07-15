"""0.45.6 — work-drain submit path, inbound debounce defer, declarative skip."""

from __future__ import annotations

import time

from palm.app.host.workplane.inbound_service import InboundBindingService
from palm.common.resource.inbound import parse_inbound_spec
from palm.core.event import EventEngine
from palm.core.work import WorkIntent


def test_parse_inbound_skip_fields() -> None:
    spec = parse_inbound_spec(
        {
            "inbound": {
                "enabled": True,
                "mode": "internal",
                "skip_self": False,
                "skip_flows": ["other-flow"],
                "skip_event_types": ["job.completed"],
                "work": {"flow_id": "react"},
            }
        }
    )
    assert spec is not None
    assert spec.skip_self is False
    assert spec.skip_flows == ("other-flow",)
    assert spec.skip_event_types == ("job.completed",)


def test_skip_internal_uses_declarative_skip_flows() -> None:
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
                    "skip_self": False,
                    "skip_flows": ["blocked-flow"],
                    "event_types": ["job.completed"],
                    "work": {"flow_id": "react"},
                }
            },
        },
    )
    svc.reload_from_definitions()
    svc.start_workers()

    events.emit("job.completed", job_id="j-1", flow="allowed")
    assert len(enqueued) == 1

    enqueued.clear()
    events.emit("job.completed", job_id="j-2", flow="blocked-flow")
    assert enqueued == []

    svc.stop()
    events.shutdown()


def test_debounce_defers_and_merges_latest_payload() -> None:
    enqueued: list[WorkIntent] = []
    svc = InboundBindingService(
        enqueue=lambda intent: enqueued.append(intent) or intent.id,
        list_resources=lambda: [{"name": "wh", "provider": "kv"}],
        get_resource=lambda name: {
            "name": name,
            "provider": "kv",
            "action": "put",
            "params": {},
            "metadata": {
                "inbound": {
                    "enabled": True,
                    "mode": "webhook",
                    "debounce_seconds": 0.2,
                    "work": {"flow_id": "react"},
                }
            },
        },
    )
    svc.reload_from_definitions()
    binding = svc.resolve("wh")
    assert binding is not None

    svc._signal(binding, {"type": "a", "payload": {"n": 1}}, source="webhook")
    svc._signal(binding, {"type": "b", "payload": {"n": 2}}, source="webhook")
    assert enqueued == []

    time.sleep(0.25)
    assert svc.flush_debounced() == 1
    assert len(enqueued) == 1
    inbound = enqueued[0].payload.get("inbound") or {}
    assert inbound.get("type") == "b"
    assert (inbound.get("payload") or {}).get("n") == 2


def test_work_drain_uses_submit_flow_body(monkeypatch) -> None:
    from palm.app import ApplicationHost, PalmSettings

    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        calls: list[dict] = []

        def _spy(body: dict) -> object:
            calls.append(body)
            return object()

        monkeypatch.setattr(host._execution.flows, "submit_flow_body", _spy)
        host.work_drain._submit_flow("noop-flow", {"source": "test"})
        assert len(calls) == 1
        assert calls[0]["flow_name"] == "noop-flow"
        assert calls[0]["metadata"]["source"] == "test"
    finally:
        host.shutdown()