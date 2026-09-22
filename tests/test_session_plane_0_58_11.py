"""0.58.11 — SI-015 owner gate: bound session must own continue instance."""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from bundles.standard.runtimes.mcp.assist.operator import rewrite_system_session_continue
from palm.system.subsystems.planes.session import (
    InstanceNotOwnedError,
    SessionClosedError,
    SessionPlaneService,
)


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_owns_instance_true_only_for_attach_list() -> None:
    plane = SessionPlaneService(storage=_storage())
    a = plane.bind().session_id
    b = plane.bind().session_id
    plane.attach_instance(a, "inst-a")
    plane.attach_instance(b, "inst-b")
    assert plane.owns_instance(a, "inst-a")
    assert not plane.owns_instance(a, "inst-b")
    assert not plane.owns_instance(a, "inst-orphan")
    assert not plane.owns_instance("", "inst-a")
    assert not plane.owns_instance(a, "")


def test_require_owned_instance_ok_and_foreign() -> None:
    plane = SessionPlaneService(storage=_storage())
    a = plane.bind().session_id
    b = plane.bind().session_id
    plane.attach_instance(a, "inst-a")
    plane.attach_instance(b, "inst-b")
    rec = plane.require_owned_instance(a, "inst-a")
    assert rec.session_id == a
    with pytest.raises(InstanceNotOwnedError, match="owned by session"):
        plane.require_owned_instance(a, "inst-b")
    with pytest.raises(InstanceNotOwnedError, match="not attached"):
        plane.require_owned_instance(a, "inst-orphan")


def test_require_owned_instance_closed_session() -> None:
    plane = SessionPlaneService(storage=_storage())
    sid = plane.bind().session_id
    plane.attach_instance(sid, "inst-1")
    plane.close(sid)
    with pytest.raises(SessionClosedError):
        plane.require_owned_instance(sid, "inst-1")


def test_active_focus_does_not_authorize_foreign() -> None:
    """Active is focus only — cannot set foreign; gate rejects foreign drive."""
    plane = SessionPlaneService(storage=_storage())
    a = plane.bind().session_id
    b = plane.bind().session_id
    plane.attach_instance(a, "inst-a")
    plane.attach_instance(b, "inst-b")
    # Cannot set active to foreign
    with pytest.raises(Exception, match="not attached"):
        plane.set_active_instance(a, "inst-b")
    # Even if we only had active, require_owned still rejects foreign
    with pytest.raises(InstanceNotOwnedError):
        plane.require_owned_instance(a, "inst-b")


def test_rewrite_rejects_foreign_instance_with_bound_session() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        bind_a = host.bind_session(surface="test-a")
        bind_b = host.bind_session(surface="test-b")
        plane = host.session_plane
        assert plane is not None
        plane.attach_instance(bind_a.session_id, "inst-a")
        plane.attach_instance(bind_b.session_id, "inst-b")

        # Owned path ok
        path, params = rewrite_system_session_continue(
            host,
            ["assist", "instance", "inst-a", "input"],
            {"session_id": bind_a.session_id, "value": "hi"},
        )
        assert path[2] == "inst-a"
        assert params["session_id"] == bind_a.session_id

        # Foreign instance under bound session A → refuse
        with pytest.raises(InstanceNotOwnedError):
            rewrite_system_session_continue(
                host,
                ["assist", "instance", "inst-b", "input"],
                {"session_id": bind_a.session_id, "value": "nope"},
            )

        # Flows path foreign refuse
        with pytest.raises(InstanceNotOwnedError):
            rewrite_system_session_continue(
                host,
                ["flows", "todo", "instance", "inst-b", "input"],
                {"session_id": bind_a.session_id, "value": "nope"},
            )
    finally:
        host.shutdown()


def test_rewrite_bare_orphan_without_bound_session_refused_0_58_15() -> None:
    """0.58.15: bare orphan continue is refused (strict attribution)."""
    from palm.system.subsystems.planes.session import SessionAttributionError

    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
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


def test_rewrite_resolved_system_session_is_owned() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        bind = host.bind_session(surface="test")
        plane = host.session_plane
        assert plane is not None
        plane.attach_instance(bind.session_id, "inst-continue")
        path, params = rewrite_system_session_continue(
            host,
            ["assist", "instance", bind.session_id, "input"],
            {"value": "hi"},
        )
        assert path[2] == "inst-continue"
        assert params["session_id"] == bind.session_id
        assert params["instance_id"] == "inst-continue"
    finally:
        host.shutdown()


def test_host_require_session_owns_instance() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        bind = host.bind_session(surface="test")
        plane = host.session_plane
        assert plane is not None
        plane.attach_instance(bind.session_id, "inst-h")
        host.require_session_owns_instance(bind.session_id, "inst-h")
        with pytest.raises(InstanceNotOwnedError):
            host.require_session_owns_instance(bind.session_id, "inst-foreign")
    finally:
        host.shutdown()


def test_doctor_snapshot_lists_owner_gate() -> None:
    plane = SessionPlaneService(storage=_storage())
    snap = plane.doctor_snapshot()
    assert snap["owner_gate"] is True
    assert "require_owned_instance" in snap["verbs"]
    assert "owns_instance" in snap["verbs"]
