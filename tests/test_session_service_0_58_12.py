"""0.58.12 — product SessionService as surface door over the session plane."""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from bundles.standard.runtimes.mcp.assist.operator import rewrite_system_session_continue
from palm.services.session import ContinueTarget, SessionService
from palm.system.subsystems.planes.session import InstanceNotOwnedError


def _host() -> ApplicationHost:
    settings = PalmSettings(load_example_definitions=False)
    return ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        storage=StorageEngine(),
    )


def test_host_wires_session_service() -> None:
    host = _host()
    host.start()
    try:
        assert host.session is not None
        assert isinstance(host.session, SessionService)
        bind = host.session.bind(surface="test")
        assert str(bind.session_id).startswith("sess-")
        assert host.session.get(bind.session_id) is not None
    finally:
        host.shutdown()


def test_continue_target_resolves_active_and_gates() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        a = svc.bind(surface="test").session_id
        b = svc.bind(surface="test").session_id
        svc.attach_instance(a, "inst-a1")
        svc.attach_instance(a, "inst-a2")
        svc.attach_instance(b, "inst-b")
        svc.set_active_instance(a, "inst-a1")

        target = svc.continue_target(session_id=a)
        assert target == ContinueTarget(session_id=a, instance_id="inst-a1")

        target2 = svc.continue_target(session_id=a, instance_id="inst-a2")
        assert target2.instance_id == "inst-a2"

        with pytest.raises(InstanceNotOwnedError):
            svc.continue_target(session_id=a, instance_id="inst-b", gate=True)
    finally:
        host.shutdown()


def test_enrich_submit_body_binds_system_session() -> None:
    host = _host()
    host.start()
    try:
        body = host.session.enrich_submit_body({"flow_name": "x"}, surface="test")
        sid = (body.get("metadata") or {}).get("session_id")
        assert sid and str(sid).startswith("sess-")
        # Preserve existing system session
        body2 = host.session.enrich_submit_body(
            {"flow_name": "y", "session_id": sid},
            surface="test",
        )
        assert body2["metadata"]["session_id"] == sid
    finally:
        host.shutdown()


def test_surface_view_includes_continue_and_refs() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind(surface="test").session_id
        svc.attach_instance(sid, "inst-1")
        view = svc.surface_view(sid)
        assert view["session_id"] == sid
        assert view["continue_instance_id"] == "inst-1"
        assert view["refs"]["instance_id"] == "inst-1"
        assert view["kind"] == "session_surface_view"
    finally:
        host.shutdown()


def test_flows_use_session_service_for_resolve_and_gate() -> None:
    host = _host()
    host.start()
    try:
        flows = host.execution.flows
        assert flows.sessions is host.session
        sid = host.session.bind(surface="test").session_id
        host.session.attach_instance(sid, "owned")
        assert flows._resolve_instance_id(sid) == "owned"
        flows._gate_bound_session_owns("owned", {"session_id": sid})
        with pytest.raises(InstanceNotOwnedError):
            flows._gate_bound_session_owns("foreign", {"session_id": sid})
    finally:
        host.shutdown()


def test_rewrite_prefers_product_session_service() -> None:
    host = _host()
    host.start()
    try:
        sid = host.session.bind(surface="test").session_id
        host.session.attach_instance(sid, "inst-x")
        host.session.attach_instance(sid, "inst-y")
        host.session.set_active_instance(sid, "inst-x")

        from types import SimpleNamespace

        ctx = SimpleNamespace(session=host.session, host=host)

        path, params = rewrite_system_session_continue(
            ctx,
            ["assist", "instance", sid],
            {},
        )
        assert path[2] == "inst-x"
        assert params["session_id"] == sid
        assert params["instance_id"] == "inst-x"

        with pytest.raises(InstanceNotOwnedError):
            rewrite_system_session_continue(
                ctx,
                ["assist", "instance", "foreign-inst"],
                {"session_id": sid},
            )
    finally:
        host.shutdown()


def test_host_bind_session_delegates_to_product() -> None:
    host = _host()
    host.start()
    try:
        bind = host.bind_session(surface="cli")
        assert str(bind.session_id).startswith("sess-")
        host.session.attach_instance(bind.session_id, "i1")
        assert host.resolve_session_continue(bind.session_id) == "i1"
        journey = host.inspect_session(bind.session_id)
        assert journey["session_id"] == bind.session_id
        assert "i1" in journey["instance_ids"]
    finally:
        host.shutdown()
