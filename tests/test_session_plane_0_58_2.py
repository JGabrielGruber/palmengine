"""0.58.2 — Session multi-attach (0..N instances) + reverse index."""

from __future__ import annotations

import pytest

from palm.core.storage import StorageEngine
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from bundles.standard.runtimes.embedded import EmbeddedRuntime
from palm.system.subsystems.planes.session import (
    InstanceAlreadyAttachedError,
    SessionClosedError,
    SessionNotFoundError,
    SessionPlaneService,
    SessionStatus,
    SessionStore,
)
from palm.system.subsystems.planes.session.store import SESSION_BY_INSTANCE_PREFIX


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_attach_many_instances_one_session() -> None:
    plane = SessionPlaneService(storage=_storage())
    sess = plane.open(session_id="sess-multi")
    assert sess.status == SessionStatus.OPEN
    assert sess.instance_ids == []

    a = plane.attach_instance("sess-multi", "inst-1")
    assert a.status == SessionStatus.ACTIVE
    assert a.instance_ids == ["inst-1"]
    assert a.active_instance_id == "inst-1"

    b = plane.attach_instance("sess-multi", "inst-2")
    assert b.instance_ids == ["inst-1", "inst-2"]
    assert b.active_instance_id == "inst-2"

    c = plane.attach_instance("sess-multi", "inst-3")
    assert c.instance_ids == ["inst-1", "inst-2", "inst-3"]
    assert c.active_instance_id == "inst-3"
    assert plane.list_instances("sess-multi") == ["inst-1", "inst-2", "inst-3"]
    # session_id is not any instance id
    assert "sess-multi" not in c.instance_ids
    assert all(i.startswith("inst-") for i in c.instance_ids)


def test_attach_instance_idempotent() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-idemp")
    plane.attach_instance("sess-idemp", "inst-x")
    again = plane.attach_instance("sess-idemp", "inst-x")
    assert again.instance_ids == ["inst-x"]


def test_detach_instance() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-det")
    plane.attach_instance("sess-det", "inst-a")
    plane.attach_instance("sess-det", "inst-b")
    left = plane.detach_instance("sess-det", "inst-a")
    assert left.instance_ids == ["inst-b"]
    # idempotent detach
    left2 = plane.detach_instance("sess-det", "inst-a")
    assert left2.instance_ids == ["inst-b"]
    empty = plane.detach_instance("sess-det", "inst-b")
    assert empty.instance_ids == []
    # remains ACTIVE after last detach (session was used)
    assert empty.status == SessionStatus.ACTIVE


def test_reverse_index_session_for_instance() -> None:
    storage = _storage()
    plane = SessionPlaneService(storage=storage)
    plane.open(session_id="sess-rev")
    plane.attach_instance("sess-rev", "inst-owned")

    assert storage.get(f"{SESSION_BY_INSTANCE_PREFIX}inst-owned") == "sess-rev"
    found = plane.session_for_instance("inst-owned")
    assert found is not None
    assert found.session_id == "sess-rev"
    assert plane.session_for_instance("inst-missing") is None

    plane.detach_instance("sess-rev", "inst-owned")
    assert storage.get(f"{SESSION_BY_INSTANCE_PREFIX}inst-owned") is None
    assert plane.session_for_instance("inst-owned") is None


def test_instance_cannot_belong_to_two_sessions() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-a")
    plane.open(session_id="sess-b")
    plane.attach_instance("sess-a", "inst-shared")
    with pytest.raises(InstanceAlreadyAttachedError):
        plane.attach_instance("sess-b", "inst-shared")
    assert plane.list_instances("sess-a") == ["inst-shared"]
    assert plane.list_instances("sess-b") == []


def test_attach_to_closed_session_refused() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-closed")
    plane.close("sess-closed")
    with pytest.raises(SessionClosedError):
        plane.attach_instance("sess-closed", "inst-late")


def test_attach_unknown_session() -> None:
    plane = SessionPlaneService(storage=_storage())
    with pytest.raises(SessionNotFoundError):
        plane.attach_instance("sess-nope", "inst-1")


def test_attach_empty_instance_id() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-empty")
    with pytest.raises(Exception):
        plane.attach_instance("sess-empty", "  ")


def test_store_put_syncs_reverse_and_delete_clears() -> None:
    storage = _storage()
    store = SessionStore(storage)
    from palm.system.subsystems.planes.session import SessionRecord

    rec = SessionRecord(
        session_id="sess-store",
        status=SessionStatus.ACTIVE,
        instance_ids=["i1", "i2"],
    )
    store.put(rec)
    assert store.session_id_for_instance("i1") == "sess-store"
    assert store.session_id_for_instance("i2") == "sess-store"

    rec.instance_ids = ["i2", "i3"]
    store.put(rec)
    assert store.session_id_for_instance("i1") is None
    assert store.session_id_for_instance("i2") == "sess-store"
    assert store.session_id_for_instance("i3") == "sess-store"

    assert store.delete("sess-store") is True
    assert store.session_id_for_instance("i2") is None
    assert store.session_id_for_instance("i3") is None


def test_doctor_snapshot_reports_multi_attach() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open(session_id="sess-doc")
    plane.attach_instance("sess-doc", "inst-d1")
    plane.attach_instance("sess-doc", "inst-d2")
    snap = plane.doctor_snapshot()
    assert snap["multi_attach"] is True
    assert "attach_instance" in snap["verbs"]
    assert snap["counts"]["active"] == 1
    assert snap["counts"]["attached_instances"] == 2


def test_embedded_runtime_multi_attach() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        plane = rt.session_plane
        assert plane is not None
        sess = plane.open(metadata={"via": "embedded-0.58.2"})
        plane.attach_instance(sess.session_id, "inst-e1")
        plane.attach_instance(sess.session_id, "inst-e2")
        got = plane.session_for_instance("inst-e1")
        assert got is not None
        assert got.session_id == sess.session_id
        assert plane.list_instances(sess.session_id) == ["inst-e1", "inst-e2"]
        # reverse key lives on runtime storage
        assert (
            rt.storage.get(f"{SESSION_BY_INSTANCE_PREFIX}inst-e1") == sess.session_id
        )
    finally:
        rt.stop()
        clear_palm_runtime()
