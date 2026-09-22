"""0.58.15 — strict attribution: start always sessioned; continue requires owner."""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from bundles.standard.runtimes.mcp.assist.operator import rewrite_system_session_continue
from palm.services.session import SessionAttributionError, SessionService
from palm.system.subsystems.planes.session import (
    InstanceNotOwnedError,
    SessionAttributionError as PlaneAttributionError,
    SessionPlaneService,
)


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def _host(*, strict: bool = True) -> ApplicationHost:
    settings = PalmSettings(
        load_example_definitions=False,
        session_strict_attribution=strict,
    )
    return ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        storage=StorageEngine(),
    )


def test_plane_require_continue_attribution_strict_orphan() -> None:
    plane = SessionPlaneService(storage=_storage())
    with pytest.raises(PlaneAttributionError, match="no owner session"):
        plane.require_continue_attribution("inst-orphan", strict=True)


def test_plane_require_continue_attribution_resolves_owner() -> None:
    plane = SessionPlaneService(storage=_storage())
    sid = plane.bind().session_id
    plane.attach_instance(sid, "inst-owned")
    bound = plane.require_continue_attribution("inst-owned", strict=True)
    assert bound == sid
    # Explicit wrong session still ownership error
    other = plane.bind().session_id
    with pytest.raises(InstanceNotOwnedError):
        plane.require_continue_attribution(
            "inst-owned", other, strict=True
        )


def test_plane_compat_strict_false_allows_bare() -> None:
    plane = SessionPlaneService(storage=_storage())
    assert plane.require_continue_attribution("inst-orphan", strict=False) is None


def test_host_strict_default_true() -> None:
    host = _host()
    host.start()
    try:
        assert isinstance(host.session, SessionService)
        assert host.session.strict_attribution is True
    finally:
        host.shutdown()


def test_rewrite_orphan_bare_instance_refused() -> None:
    """0.58.15: bare orphan continue is no longer a happy path."""
    host = _host()
    host.start()
    try:
        with pytest.raises(SessionAttributionError, match="no owner session"):
            rewrite_system_session_continue(
                host,
                ["assist", "instance", "inst-orphan", "input"],
                {"value": "legacy"},
            )
    finally:
        host.shutdown()


def test_rewrite_owned_instance_without_params_session_resolves() -> None:
    """Owned instance + no client session_id → plane owner is bind truth."""
    host = _host()
    host.start()
    try:
        sid = host.session.bind(surface="test").session_id
        host.session.attach_instance(sid, "inst-owned")
        path, params = rewrite_system_session_continue(
            host,
            ["assist", "instance", "inst-owned", "input"],
            {"value": "ok"},
        )
        assert path[2] == "inst-owned"
        assert params["session_id"] == sid
    finally:
        host.shutdown()


def test_rewrite_foreign_with_bound_session_still_refused() -> None:
    host = _host()
    host.start()
    try:
        a = host.session.bind(surface="a").session_id
        b = host.session.bind(surface="b").session_id
        host.session.attach_instance(a, "inst-a")
        host.session.attach_instance(b, "inst-b")
        with pytest.raises(InstanceNotOwnedError):
            rewrite_system_session_continue(
                host,
                ["assist", "instance", "inst-b", "input"],
                {"session_id": a, "value": "nope"},
            )
    finally:
        host.shutdown()


def test_compat_flag_allows_bare_orphan() -> None:
    host = _host(strict=False)
    host.start()
    try:
        assert host.session.strict_attribution is False
        path, params = rewrite_system_session_continue(
            host,
            ["assist", "instance", "inst-orphan", "input"],
            {"value": "compat"},
        )
        assert path[2] == "inst-orphan"
    finally:
        host.shutdown()


def test_continue_target_strict_resolves_owner() -> None:
    host = _host()
    host.start()
    try:
        sid = host.session.bind().session_id
        host.session.attach_instance(sid, "i1")
        target = host.session.continue_target(instance_id="i1")
        assert target.session_id == sid
        assert target.instance_id == "i1"
        with pytest.raises(SessionAttributionError):
            host.session.continue_target(instance_id="orphan-x")
    finally:
        host.shutdown()


def test_flows_gate_orphan_unknown_defers_known_owned_injects() -> None:
    """Product gate: unknown id defers (404 later); owned injects session."""
    host = _host()
    host.start()
    try:
        # Unknown orphan — allow_unknown default → no raise (REST not-found path)
        assert host.execution.flows._gate_bound_session_owns("orphan-y", {}) is None
        sid = host.session.bind().session_id
        host.session.attach_instance(sid, "owned-z")
        host.execution.flows._gate_bound_session_owns("owned-z", {})
        params: dict = {}
        host.session.gate_bound_session_owns("owned-z", params)
        assert params["session_id"] == sid
        # Explicit refuse of bare orphan (operator / continue_target)
        with pytest.raises(SessionAttributionError):
            host.session.gate_bound_session_owns(
                "orphan-y", {}, allow_unknown=False
            )
    finally:
        host.shutdown()


def test_enrich_submit_body_still_attributes_start() -> None:
    host = _host()
    host.start()
    try:
        body = host.session.enrich_submit_body({"flow_name": "x"}, surface="test")
        assert str(body["metadata"]["session_id"]).startswith("sess-")
    finally:
        host.shutdown()


def test_doctor_snapshot_lists_strict_attribution() -> None:
    plane = SessionPlaneService(storage=_storage())
    snap = plane.doctor_snapshot()
    assert snap["strict_attribution"] is True
    assert "require_continue_attribution" in snap["verbs"]
