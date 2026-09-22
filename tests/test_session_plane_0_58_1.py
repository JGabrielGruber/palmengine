"""0.58.1 — Session plane system seat (types + StorageEngine store + runtime)."""

from __future__ import annotations

import pytest

from palm.core.storage import StorageEngine
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from bundles.standard.runtimes.embedded import EmbeddedRuntime
from palm.system.subsystems.planes.session import (
    SessionNotFoundError,
    SessionPlaneService,
    SessionRecord,
    SessionStatus,
    SessionStore,
    bind_session_plane_to_runtime,
    new_session_id,
)
from palm.system.subsystems.planes.session.types import SessionRecord as SessionRecordDirect


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_session_id_is_not_instance_shaped() -> None:
    sid = new_session_id()
    assert sid.startswith("sess-")
    assert len(sid) > 10


def test_session_record_roundtrip_and_multi_instance_field() -> None:
    rec = SessionRecord(
        session_id="sess-demo",
        status=SessionStatus.OPEN,
        instance_ids=["inst-a", "inst-b"],
        metadata={"surface": "test"},
    )
    data = rec.to_dict()
    assert data["kind"] == "session"
    assert data["session_id"] == "sess-demo"
    assert data["instance_ids"] == ["inst-a", "inst-b"]
    assert data["session_id"] != data["instance_ids"][0]
    back = SessionRecordDirect.from_dict(data)
    assert back.session_id == rec.session_id
    assert back.instance_ids == ["inst-a", "inst-b"]
    assert back.status == SessionStatus.OPEN


def test_session_store_uses_storage_engine() -> None:
    storage = _storage()
    store = SessionStore(storage)
    rec = SessionRecord(session_id="sess-se", status=SessionStatus.OPEN)
    store.put(rec)
    assert storage.get("palm:session:entry:sess-se") is not None
    assert "sess-se" in storage.get("palm:session:index")
    loaded = store.get("sess-se")
    assert loaded is not None
    assert loaded.session_id == "sess-se"


def test_session_plane_open_get_close_list() -> None:
    plane = SessionPlaneService(storage=_storage())
    a = plane.open(metadata={"k": 1})
    assert a.status == SessionStatus.OPEN
    assert a.session_id.startswith("sess-")
    assert a.instance_ids == []
    got = plane.get(a.session_id)
    assert got is not None
    assert got.session_id == a.session_id

    b = plane.open(session_id="sess-fixed")
    assert b.session_id == "sess-fixed"
    again = plane.open(session_id="sess-fixed")
    assert again.session_id == "sess-fixed"

    closed = plane.close(a.session_id)
    assert closed.status == SessionStatus.CLOSED
    assert plane.close(a.session_id).status == SessionStatus.CLOSED

    open_only = plane.list_sessions(include_closed=False)
    assert all(r.status != SessionStatus.CLOSED for r in open_only)
    assert any(r.session_id == "sess-fixed" for r in open_only)

    with pytest.raises(SessionNotFoundError):
        plane.require("sess-missing")


def test_session_plane_doctor_snapshot() -> None:
    plane = SessionPlaneService(storage=_storage())
    plane.open()
    plane.open()
    snap = plane.doctor_snapshot()
    assert snap["plane"] == "session"
    assert snap["store"] == "storage_engine"
    assert snap["storage_backend"] == "memory"
    assert "open" in snap["verbs"]
    assert snap["counts"]["total"] == 2


def test_bind_session_plane_helper() -> None:
    from palm.system.interfaces.install import SystemInstall

    eng = _storage()

    class _Rt:
        def __init__(self, storage: StorageEngine) -> None:
            self.storage = storage
            self.orchestration = type("O", (), {"jobs": {}})()
            self._planes = None
            self._install = SystemInstall()

        @property
        def install(self) -> SystemInstall:
            return self._install

        def bind_system_install(self) -> SystemInstall:
            return self._install.bind(
                orchestration=self.orchestration,
                storage=self.storage,
                submit=lambda *a, **k: None,
                able=lambda: True,
            )

        @property
        def session_plane(self):
            if self._planes is None:
                return None
            return self._planes.get("session")

    rt = _Rt(eng)
    plane = bind_session_plane_to_runtime(rt)
    assert plane.is_attached
    assert rt.session_plane is plane
    assert rt._planes is not None
    assert rt._planes.get("session") is plane
    rec = plane.open(session_id="sess-bind")
    assert plane.get(rec.session_id) is not None


def test_embedded_runtime_exposes_session_plane() -> None:
    rt = EmbeddedRuntime()
    assert rt.session_plane is None
    rt.start()
    try:
        assert rt.session_plane is not None
        assert rt.session_plane.is_attached
        rec = rt.session_plane.open(metadata={"via": "embedded"})
        assert rec.session_id.startswith("sess-")
        assert rt.session_plane.get(rec.session_id) is not None
        # Records live on runtime StorageEngine (same keys as work plane style).
        assert rt.storage.get(f"palm:session:entry:{rec.session_id}") is not None
        snap = rt.session_plane.doctor_snapshot()
        assert snap["session_plane_attached"] is True
        assert snap["store"] == "storage_engine"
        assert snap["counts"]["total"] >= 1
    finally:
        rt.stop()
        clear_palm_runtime()
    assert rt.session_plane is None
