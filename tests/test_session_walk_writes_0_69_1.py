"""0.69.1 — walk-write seam: stamp / replace a named session-metadata instance id.

Floor allow is degenerate: owner session + attached instance.
Callers pass the key (0.69.8). Attach, focus, and owner check stay
geometry — they do not stamp. Interface type unnamed (VISION-NAVIGATOR §5).
"""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from palm.core.storage import StorageEngine
from palm.system.subsystems.planes.session import (
    InstanceNotOwnedError,
    SessionClosedError,
    SessionPlaneError,
    SessionPlaneService,
)

KEY = "walk_instance_id"


def _plane() -> SessionPlaneService:
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    return SessionPlaneService(storage=storage)


def test_stamp_writes_named_key_when_attached() -> None:
    plane = _plane()
    rec = plane.open()
    plane.attach_instance(rec.session_id, "inst-guide")

    stamped = plane.stamp(rec.session_id, KEY, "inst-guide")

    assert stamped.metadata[KEY] == "inst-guide"
    assert plane.get_metadata(rec.session_id)[KEY] == "inst-guide"


def test_attach_does_not_stamp_named_key() -> None:
    plane = _plane()
    rec = plane.open()
    plane.attach_instance(rec.session_id, "inst-guide")

    assert KEY not in plane.get_metadata(rec.session_id)


def test_focus_does_not_stamp_named_key() -> None:
    plane = _plane()
    rec = plane.open()
    plane.attach_instance(rec.session_id, "inst-guide")
    plane.attach_instance(rec.session_id, "inst-title")
    plane.set_active_instance(rec.session_id, "inst-guide")

    assert KEY not in plane.get_metadata(rec.session_id)
    assert plane.active_instance(rec.session_id) == "inst-guide"


def test_stamp_does_not_steal_continue_focus() -> None:
    plane = _plane()
    rec = plane.open()
    plane.attach_instance(rec.session_id, "inst-guide")
    plane.attach_instance(rec.session_id, "inst-title")
    assert plane.active_instance(rec.session_id) == "inst-title"

    plane.stamp(rec.session_id, KEY, "inst-guide")

    assert plane.active_instance(rec.session_id) == "inst-title"
    assert plane.get_metadata(rec.session_id)[KEY] == "inst-guide"


def test_stamp_refuses_unattached_instance() -> None:
    plane = _plane()
    rec = plane.open()
    plane.attach_instance(rec.session_id, "inst-owned")

    with pytest.raises(InstanceNotOwnedError):
        plane.stamp(rec.session_id, KEY, "inst-foreign")

    assert KEY not in plane.get_metadata(rec.session_id)


def test_stamp_if_absent_refuses_different_instance() -> None:
    plane = _plane()
    rec = plane.open()
    plane.attach_instance(rec.session_id, "inst-guide")
    plane.attach_instance(rec.session_id, "inst-other")
    plane.stamp(rec.session_id, KEY, "inst-guide")

    with pytest.raises(SessionPlaneError, match="use replace"):
        plane.stamp(rec.session_id, KEY, "inst-other")

    assert plane.get_metadata(rec.session_id)[KEY] == "inst-guide"


def test_stamp_same_instance_is_idempotent() -> None:
    plane = _plane()
    rec = plane.open()
    plane.attach_instance(rec.session_id, "inst-guide")
    first = plane.stamp(rec.session_id, KEY, "inst-guide")
    again = plane.stamp(rec.session_id, KEY, "inst-guide")

    assert first.metadata[KEY] == "inst-guide"
    assert again.metadata[KEY] == "inst-guide"


def test_replace_overwrites_when_attached() -> None:
    plane = _plane()
    rec = plane.open()
    plane.attach_instance(rec.session_id, "inst-guide")
    plane.attach_instance(rec.session_id, "inst-new-guide")
    plane.stamp(rec.session_id, KEY, "inst-guide")

    replaced = plane.replace(rec.session_id, KEY, "inst-new-guide")

    assert replaced.metadata[KEY] == "inst-new-guide"


def test_replace_refuses_unattached_instance() -> None:
    plane = _plane()
    rec = plane.open()
    plane.attach_instance(rec.session_id, "inst-guide")
    plane.stamp(rec.session_id, KEY, "inst-guide")

    with pytest.raises(InstanceNotOwnedError):
        plane.replace(rec.session_id, KEY, "inst-title")

    assert plane.get_metadata(rec.session_id)[KEY] == "inst-guide"


def test_stamp_refuses_closed_session() -> None:
    plane = _plane()
    rec = plane.open()
    plane.attach_instance(rec.session_id, "inst-guide")
    plane.close(rec.session_id)

    with pytest.raises(SessionClosedError):
        plane.stamp(rec.session_id, KEY, "inst-guide")


def test_session_service_door_stamps_and_replaces() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="embedded", origin="test")
        sid = bound.session_id
        svc.attach_instance(sid, "inst-guide")
        svc.attach_instance(sid, "inst-title")

        stamped = svc.stamp(sid, KEY, "inst-guide")
        assert stamped.metadata[KEY] == "inst-guide"
        assert stamped.session_id == sid
        assert svc.active_instance(sid) == "inst-title"

        svc.attach_instance(sid, "inst-new-guide")
        replaced = svc.replace(sid, KEY, "inst-new-guide")
        assert replaced.metadata[KEY] == "inst-new-guide"
    finally:
        host.shutdown()
