"""0.58.16 — inherit-or-service reactive start (finish SI-011)."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.common.triggers.registry import (
    TriggerRegistry,
    _system_session_from_signal,
    _with_inherited_session,
)
from palm.core.storage import StorageEngine
from palm.services.session import SessionService, service_session_id


def _host() -> ApplicationHost:
    settings = PalmSettings(load_example_definitions=False)
    return ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        storage=StorageEngine(),
    )


def test_system_session_from_signal_only_sess() -> None:
    assert _system_session_from_signal({"session_id": "sess-abc"}) == "sess-abc"
    assert _system_session_from_signal({"session_id": "inst-1"}) is None
    assert _system_session_from_signal({}) is None


def test_trigger_on_flow_inherits_session_from_event() -> None:
    from palm.common.triggers.parse import TriggerSpec

    reg = TriggerRegistry()
    reg._specs = [
        (
            "child-flow",
            TriggerSpec(
                kind="on_flow",
                work_flow_id="child-flow",
                source_flow="parent-flow",
                when="succeeded",
            ),
        )
    ]
    intents = reg.on_event(
        "flow.session.succeeded",
        {
            "flow_id": "parent-flow",
            "session_id": "sess-parent-walk",
            "instance_id": "inst-1",
        },
    )
    assert len(intents) == 1
    assert intents[0].payload.get("session_id") == "sess-parent-walk"
    assert intents[0].payload.get("trigger") == "on_flow"


def test_trigger_without_session_has_no_session_id() -> None:
    from palm.common.triggers.parse import TriggerSpec

    reg = TriggerRegistry()
    reg._specs = [
        (
            "analytics",
            TriggerSpec(
                kind="on_resource",
                work_flow_id="analytics",
                resource="palm-todos",
            ),
        )
    ]
    intents = reg.on_event(
        "resource.changed",
        {"resource_ref": "palm-todos", "action": "put"},
    )
    assert len(intents) == 1
    assert "session_id" not in intents[0].payload


def test_enrich_reactive_start_inherits() -> None:
    host = _host()
    host.start()
    try:
        svc: SessionService = host.session
        parent = svc.bind(surface="test").session_id
        body = {
            "flow_name": "child",
            "metadata": {"session_id": parent, "trigger": "on_flow"},
        }
        out = svc.enrich_reactive_start(
            body, origin="work-drain:child", surface="work-drain"
        )
        assert out["metadata"]["session_id"] == parent
        assert out["metadata"]["session_attribution"] == "inherit"
        # Must not replace with service session
        assert out["metadata"]["session_id"] != service_session_id(
            "work-drain:child"
        )
    finally:
        host.shutdown()


def test_enrich_reactive_start_service_when_no_signal() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        out = svc.enrich_reactive_start(
            {"flow_name": "analytics", "metadata": {"trigger": "on_resource"}},
            origin="work-drain:analytics",
        )
        assert out["metadata"]["session_id"] == service_session_id(
            "work-drain:analytics"
        )
        assert out["metadata"]["session_attribution"] == "service"
        assert out["metadata"]["session_origin"] == "work-drain:analytics"
    finally:
        host.shutdown()


def test_reactive_origin_kinds() -> None:
    assert SessionService.reactive_origin(
        "todo-analytics", {"trigger": "schedule"}
    ) == "schedule:todo-analytics"
    assert SessionService.reactive_origin(
        "x", {"trigger": "inbound", "inbound_resource": "webhook-a"}
    ) == "inbound:webhook-a"
    assert SessionService.reactive_origin(
        "todo-analytics", {"trigger": "on_resource"}
    ) == "work-drain:todo-analytics"
    assert SessionService.reactive_origin(None, {}) == "work-drain"


def test_inherit_or_service_session_helper() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        parent = svc.bind().session_id
        assert (
            svc.inherit_or_service_session(
                session_id=parent, origin="work-drain:x"
            )
            == parent
        )
        assert svc.inherit_or_service_session(
            origin="schedule:nightly"
        ) == service_session_id("schedule:nightly")
    finally:
        host.shutdown()


def test_coordinator_submit_inherits_from_intent_payload() -> None:
    """Work drain path: payload.session_id → same system subject on submit body."""
    host = _host()
    host.start()
    try:
        svc = host.session
        parent = svc.bind(surface="walk").session_id
        # Simulate coordinator origin + enrich (same as _submit)
        body = {
            "flow_name": "child",
            "metadata": {
                "trigger": "on_flow",
                "session_id": parent,
                "source_flow": "parent",
            },
        }
        origin = svc.reactive_origin("child", body["metadata"])
        enriched = svc.enrich_reactive_start(body, origin=origin)
        assert enriched["metadata"]["session_id"] == parent
        assert enriched["metadata"]["session_attribution"] == "inherit"
    finally:
        host.shutdown()


def test_coordinator_submit_service_for_schedule_origin() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        meta = {"trigger": "schedule"}
        origin = svc.reactive_origin("nightly-report", meta)
        assert origin == "schedule:nightly-report"
        enriched = svc.enrich_reactive_start(
            {"flow_name": "nightly-report", "metadata": meta},
            origin=origin,
        )
        assert enriched["metadata"]["session_id"] == service_session_id(origin)
        assert enriched["metadata"]["session_attribution"] == "service"
    finally:
        host.shutdown()


def test_with_inherited_session_helper() -> None:
    base = {"trigger": "on_flow", "depth": 1}
    assert _with_inherited_session(base, {"session_id": "sess-x"})[
        "session_id"
    ] == "sess-x"
    assert "session_id" not in _with_inherited_session(base, {"session_id": "inst-1"})
