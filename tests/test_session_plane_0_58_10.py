"""0.58.10 — Plane-owned active_instance_id (continue focus)."""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from palm.system.subsystems.planes.session import (
    SessionPlaneError,
    SessionPlaneService,
    SessionRecord,
    SessionStatus,
    SessionStore,
)


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_attach_sets_active_to_new_instance() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-act")
    a = plane.attach_instance("sess-act", "inst-1")
    assert a.active_instance_id == "inst-1"
    b = plane.attach_instance("sess-act", "inst-2")
    assert b.active_instance_id == "inst-2"
    assert b.instance_ids == ["inst-1", "inst-2"]
    # session subject ≠ instance
    assert a.session_id != a.active_instance_id


def test_reattach_does_not_steal_active() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-re")
    plane.attach_instance("sess-re", "inst-a")
    plane.attach_instance("sess-re", "inst-b")
    plane.set_active_instance("sess-re", "inst-a")
    again = plane.attach_instance("sess-re", "inst-b")
    assert again.active_instance_id == "inst-a"


def test_set_active_instance_must_be_attached() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-set")
    plane.attach_instance("sess-set", "inst-1")
    with pytest.raises(SessionPlaneError, match="not attached"):
        plane.set_active_instance("sess-set", "inst-missing")
    rec = plane.set_active_instance("sess-set", "inst-1")
    assert rec.active_instance_id == "inst-1"


def test_detach_active_repoints_to_last_remaining() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-det")
    plane.attach_instance("sess-det", "inst-a")
    plane.attach_instance("sess-det", "inst-b")
    plane.attach_instance("sess-det", "inst-c")
    # active is inst-c (last attach)
    left = plane.detach_instance("sess-det", "inst-c")
    assert left.instance_ids == ["inst-a", "inst-b"]
    assert left.active_instance_id == "inst-b"
    empty = plane.detach_instance("sess-det", "inst-b")
    empty = plane.detach_instance("sess-det", "inst-a")
    assert empty.instance_ids == []
    assert empty.active_instance_id is None


def test_detach_non_active_keeps_focus() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-keep")
    plane.attach_instance("sess-keep", "inst-a")
    plane.attach_instance("sess-keep", "inst-b")
    plane.set_active_instance("sess-keep", "inst-a")
    left = plane.detach_instance("sess-keep", "inst-b")
    assert left.active_instance_id == "inst-a"


def test_resolve_continue_prefers_active_over_last() -> None:
    plane = SessionPlaneService(storage=_storage())
    sid = plane.bind().session_id
    plane.attach_instance(sid, "inst-1")
    plane.attach_instance(sid, "inst-2")
    # New attach made inst-2 active
    assert plane.resolve_continue_instance(sid) == "inst-2"
    plane.set_active_instance(sid, "inst-1")
    assert plane.resolve_continue_instance(sid) == "inst-1"
    assert plane.active_instance(sid) == "inst-1"


def test_clear_active_instance_falls_back_to_last() -> None:
    plane = SessionPlaneService(storage=_storage())
    sid = plane.bind().session_id
    plane.attach_instance(sid, "inst-1")
    plane.attach_instance(sid, "inst-2")
    plane.clear_active_instance(sid)
    assert plane.active_instance(sid) is None
    # No active → last attached
    assert plane.resolve_continue_instance(sid) == "inst-2"


def test_inspect_and_bind_expose_active() -> None:
    plane = SessionPlaneService(storage=_storage())
    bind = plane.bind(surface="test")
    assert bind.active_instance_id is None
    plane.attach_instance(bind.session_id, "inst-x")
    rebound = plane.bind(session_id=bind.session_id, create=False)
    assert rebound.active_instance_id == "inst-x"
    assert rebound.to_dict()["active_instance_id"] == "inst-x"

    view = plane.inspect(bind.session_id)
    assert view["active_instance_id"] == "inst-x"
    assert view["session_id"] == bind.session_id
    assert view["session_id"] != view["active_instance_id"]


def test_record_roundtrip_active_instance() -> None:
    store = SessionStore(_storage())
    rec = SessionRecord(
        session_id="sess-rt",
        status=SessionStatus.ACTIVE,
        instance_ids=["i1", "i2"],
        active_instance_id="i1",
    )
    store.put(rec)
    back = store.get("sess-rt")
    assert back is not None
    assert back.active_instance_id == "i1"
    assert back.to_dict()["active_instance_id"] == "i1"


def test_legacy_record_without_active_seeds_last() -> None:
    data = {
        "session_id": "sess-legacy",
        "status": "active",
        "instance_ids": ["old-1", "old-2"],
        "metadata": {},
    }
    rec = SessionRecord.from_dict(data)
    assert rec.active_instance_id == "old-2"


def test_host_resolve_continue_uses_active() -> None:
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
        plane.attach_instance(bind.session_id, "inst-h1")
        plane.attach_instance(bind.session_id, "inst-h2")
        plane.set_active_instance(bind.session_id, "inst-h1")
        assert host.resolve_session_continue(bind.session_id) == "inst-h1"
    finally:
        host.shutdown()


def test_doctor_reports_active_instance_flag() -> None:
    plane = SessionPlaneService(storage=_storage())
    snap = plane.doctor_snapshot()
    assert snap.get("active_instance") is True
    assert "set_active_instance" in snap["verbs"]
