"""0.43 — inbound as ResourceDefinition.metadata.inbound."""

from __future__ import annotations

from palm.app import ApplicationHost, PalmSettings
from palm.common.resource.inbound import is_inbound_enabled, parse_inbound_spec
from palm.definitions import FlowDefinition, ResourceDefinition


def test_parse_inbound_absent() -> None:
    assert parse_inbound_spec({}) is None
    assert parse_inbound_spec(None) is None
    assert not is_inbound_enabled({})


def test_parse_inbound_webhook() -> None:
    spec = parse_inbound_spec(
        {
            "inbound": {
                "enabled": True,
                "mode": "webhook",
                "path": "demo",
                "work": {"flow_id": "on-inbound-webhook"},
                "coalesce_field": "id",
            }
        }
    )
    assert spec is not None
    assert spec.enabled
    assert spec.mode == "webhook"
    assert spec.path == "demo"
    assert spec.work.target == "on-inbound-webhook"
    assert is_inbound_enabled(
        {"inbound": {"enabled": True, "work": {"flow_id": "x"}}}
    )


def test_parse_inbound_no_work_disables() -> None:
    spec = parse_inbound_spec({"inbound": {"enabled": True, "mode": "webhook"}})
    assert spec is not None
    assert spec.enabled is False


def test_webhook_enqueues_work_intent() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        repo = host.app.repository()
        repo.save_resource(
            ResourceDefinition(
                name="inbound-webhook-demo",
                provider="kv",
                action="put",
                resource_id="inbound/x",
                params={},
                metadata={
                    "inbound": {
                        "enabled": True,
                        "mode": "webhook",
                        "work": {"flow_id": "on-inbound-webhook"},
                        "coalesce_field": "id",
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
                        {
                            "slug": "ack",
                            "kind": "introduction",
                            "prompt": "ok",
                        }
                    ]
                },
            )
        )
        n = host.reload_inbound_bindings()
        assert n >= 1
        bindings = host.inbound.list_bindings()
        assert any(b["resource_name"] == "inbound-webhook-demo" for b in bindings)

        result = host.inbound.handle_webhook(
            "inbound-webhook-demo",
            body={"id": "evt-1", "hello": True},
            headers={},
        )
        assert result["accepted"] is True
        assert result.get("intent_id")

        pending = host.work_drain.store.pending_count()
        assert pending >= 1

        processed = host.tick_work(limit=5)
        assert processed >= 1
    finally:
        host.shutdown()


def test_webhook_secret_rejects() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        repo = host.app.repository()
        repo.save_resource(
            ResourceDefinition(
                name="sec-in",
                provider="kv",
                action="put",
                resource_id="inbound/sec",
                params={"inbound_secret": "s3cret"},
                metadata={
                    "inbound": {
                        "enabled": True,
                        "mode": "webhook",
                        "secret_header": "X-Palm-Inbound-Secret",
                        "secret_param": "inbound_secret",
                        "work": {"flow_id": "on-inbound-webhook"},
                    }
                },
            )
        )
        repo.save_flow(
            FlowDefinition(
                name="on-inbound-webhook",
                pattern="wizard",
                options={"steps": [{"slug": "a", "kind": "introduction", "prompt": "x"}]},
            )
        )
        host.reload_inbound_bindings()
        try:
            host.inbound.handle_webhook("sec-in", body={}, headers={})
            raise AssertionError("expected PermissionError")
        except PermissionError:
            pass
        ok = host.inbound.handle_webhook(
            "sec-in",
            body={},
            headers={"X-Palm-Inbound-Secret": "s3cret"},
        )
        assert ok["accepted"] is True
    finally:
        host.shutdown()


def test_control_plane_includes_inbound() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        status = host.control_plane_status()
        assert "inbound_count" in status
        assert "inbound_bindings" in status
    finally:
        host.shutdown()
