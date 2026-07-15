"""0.44 — inbound store inbox, poll mode, stream workers."""

from __future__ import annotations

from unittest.mock import MagicMock

from palm.app import ApplicationHost, PalmSettings
from palm.app.host.workplane.inbound_service import InboundBindingService
from palm.common.resource.inbound import parse_inbound_spec
from palm.core.work import WorkIntent
from palm.definitions import FlowDefinition, ResourceDefinition


def test_parse_inbound_store_fields() -> None:
    spec = parse_inbound_spec(
        {
            "inbound": {
                "enabled": True,
                "mode": "webhook",
                "store_resource": "inbound-inbox",
                "store_action": "put",
                "work": {"flow_id": "on-inbound-webhook"},
            }
        }
    )
    assert spec is not None
    assert spec.store_resource == "inbound-inbox"
    assert spec.store_action == "put"


def test_webhook_store_resource_persists_inbox() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        repo = host.app.repository()
        repo.save_resource(
            ResourceDefinition(
                name="inbound-inbox",
                provider="kv",
                action="put",
                resource_id="inbound/inbox",
                params={"namespace": "palm", "backend": "memory"},
            )
        )
        repo.save_resource(
            ResourceDefinition(
                name="wh-with-store",
                provider="kv",
                action="put",
                resource_id="inbound/wh",
                params={},
                metadata={
                    "inbound": {
                        "enabled": True,
                        "mode": "webhook",
                        "store_resource": "inbound-inbox",
                        "store_action": "put",
                        "work": {"flow_id": "on-inbound-webhook"},
                    }
                },
            )
        )
        repo.save_flow(
            FlowDefinition(
                name="on-inbound-webhook",
                pattern="wizard",
                options={
                    "steps": [
                        {"slug": "ack", "kind": "introduction", "prompt": "ok"},
                    ]
                },
            )
        )
        host.reload_inbound_bindings()
        result = host.inbound.handle_webhook(
            "wh-with-store",
            body={"id": "evt-store-1", "hello": True},
            headers={},
        )
        assert result["accepted"] is True
        assert result.get("stored") is True
        assert result.get("store_resource") == "inbound-inbox"

        got = host.invoke_resource("inbound-inbox", action="get")
        assert got.success
        stored = got.data
        assert isinstance(stored, dict)
        envelope = stored.get("value") if isinstance(stored.get("value"), dict) else stored
        assert envelope.get("payload", {}).get("id") == "evt-store-1"

        pending = host.work_drain.store.pending_count()
        assert pending >= 1
    finally:
        host.shutdown()


def test_poll_mode_invokes_pull_resource() -> None:
    enqueued: list[WorkIntent] = []
    invoke_calls: list[tuple[str, str | None]] = []

    def _enqueue(intent: WorkIntent) -> str:
        enqueued.append(intent)
        return "intent-poll-1"

    def _invoke(resource_ref: str, *, action: str | None = None, params=None) -> object:
        invoke_calls.append((resource_ref, action))
        from palm.core.resource.result import ProviderResult

        return ProviderResult.ok({"items": [{"id": "a"}]})

    svc = InboundBindingService(
        enqueue=_enqueue,
        list_resources=lambda: [{"name": "poll-res", "provider": "kv"}],
        get_resource=lambda name: {
            "name": name,
            "provider": "kv",
            "action": "get",
            "resource_id": "poll/key",
            "params": {},
            "metadata": {
                "inbound": {
                    "enabled": True,
                    "mode": "poll",
                    "work": {"flow_id": "react"},
                }
            },
        },
        invoke_resource=_invoke,
    )
    svc.reload_from_definitions()
    envelope = svc._poll_once(svc.resolve("poll-res"))
    assert envelope is not None
    assert envelope["source"] == "poll"
    intent_id, meta = svc._signal(svc.resolve("poll-res"), envelope, source="poll")
    assert intent_id == "intent-poll-1"
    assert invoke_calls == [("poll-res", "get")]
    assert enqueued[0].target == "react"
    assert enqueued[0].payload.get("source") == "poll"


def test_store_envelope_invokes_inbox() -> None:
    invoke = MagicMock()
    invoke.return_value = type(
        "R", (), {"success": True, "data": None, "error": None}
    )()

    svc = InboundBindingService(
        enqueue=lambda intent: "id-1",
        get_resource=lambda name: {
            "name": name,
            "provider": "kv",
            "action": "put",
            "resource_id": "inbound/inbox",
            "params": {"namespace": "palm"},
        },
        invoke_resource=invoke,
    )
    binding = type(
        "B",
        (),
        {
            "resource_name": "wh",
            "provider": "kv",
            "spec": parse_inbound_spec(
                {
                    "inbound": {
                        "enabled": True,
                        "store_resource": "inbound-inbox",
                        "store_action": "put",
                        "work": {"flow_id": "x"},
                    }
                }
            ),
            "definition": {},
        },
    )()
    meta = svc._store_envelope(binding, {"payload": {"id": 1}})
    assert meta["stored"] is True
    invoke.assert_called_once()
    call = invoke.call_args
    assert call.args[0] == "inbound-inbox"
    assert call.kwargs["action"] == "put"
    assert call.kwargs["params"]["value"]["payload"]["id"] == 1