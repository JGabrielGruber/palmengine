"""0.38 — EventJournal append, offsets, compact, redrive."""

from __future__ import annotations

from palm.common.events import (
    EventJournal,
    compact_key_for_resource_changed,
    wire_event_journal,
)
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_append_and_read_after() -> None:
    j = EventJournal(_storage())
    o1 = j.append("resource.changed", {"resource_ref": "a", "action": "put"})
    o2 = j.append("resource.changed", {"resource_ref": "b", "action": "put"})
    assert o1 == 1 and o2 == 2
    batch = j.read_after(0, limit=10)
    assert [e.offset for e in batch] == [1, 2]
    assert j.read_after(1, limit=10)[0].offset == 2


def test_named_consumer_offsets() -> None:
    j = EventJournal(_storage())
    j.append("resource.changed", {"resource_ref": "x", "action": "put"})
    j.append("resource.changed", {"resource_ref": "y", "action": "put"})
    batch = j.consume("work_drain", limit=1, auto_commit=True)
    assert len(batch) == 1
    assert j.get_consumer_offset("work_drain") == 1
    batch2 = j.consume("work_drain", limit=10)
    assert len(batch2) == 1
    assert batch2[0].offset == 2


def test_compact_key_latest() -> None:
    j = EventJournal(_storage())
    key = compact_key_for_resource_changed({"resource_ref": "palm-todos", "resource_id": ""})
    assert key is not None
    j.append("resource.changed", {"resource_ref": "palm-todos"}, compact_key=key)
    j.append("resource.changed", {"resource_ref": "palm-todos"}, compact_key=key)
    assert j.compacted_offset(key) == 2


def test_redrive_does_not_move_consumer() -> None:
    j = EventJournal(_storage())
    j.append("a", {})
    j.append("b", {})
    j.commit_consumer_offset("c1", 2)
    rows = j.redrive(from_offset=0, limit=10)
    assert len(rows) == 2
    assert j.get_consumer_offset("c1") == 2


def test_wire_journal_interceptor() -> None:
    storage = _storage()
    engine = EventEngine()
    engine.initialize()
    journal, _ = wire_event_journal(engine, storage)
    engine.emit("resource.changed", resource_ref="palm-todos", action="put")
    assert journal.latest_offset() >= 1
    entry = journal.get(journal.latest_offset())
    assert entry is not None
    assert entry.event_type == "resource.changed"
    engine.shutdown()


def test_host_control_plane_status() -> None:
    from palm.app.host.application_host import ApplicationHost
    from palm.app.host.roles import DeploymentProfile
    from palm.app.settings import PalmSettings

    with ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=DeploymentProfile.all_in_one(),
    ) as host:
        assert host.event_journal is not None
        host.event.emit("resource.changed", resource_ref="x", action="put")
        status = host.control_plane_status()
        assert "work_pending" in status
        assert status["journal"]["latest_offset"] >= 1
        redrive = host.redrive_journal(from_offset=0, limit=10)
        assert any(e.get("event_type") == "resource.changed" for e in redrive)
