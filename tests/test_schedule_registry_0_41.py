"""0.41.1 — durable interval schedules → WorkIntent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from palm.common.work.schedule import ScheduleRegistry
from palm.common.work.store import WorkIntentStore
from palm.core.storage import StorageEngine


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_schedule_tick_enqueues_and_advances() -> None:
    storage = _storage()
    work = WorkIntentStore(storage)
    sched = ScheduleRegistry(storage, work)
    sched.upsert("nightly", flow_id="todo-analytics", interval_seconds=3600)
    # force due
    entry = storage.get("palm:schedule:entry:nightly")
    assert isinstance(entry, dict)
    past = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    entry["next_fire_at"] = past
    storage.set("palm:schedule:entry:nightly", entry)

    fired = sched.tick()
    assert len(fired) == 1
    assert work.pending_count() >= 1

    # not due again immediately
    fired2 = sched.tick()
    assert fired2 == []

    # next_fire in the future
    entry2 = storage.get("palm:schedule:entry:nightly")
    assert isinstance(entry2, dict)
    nxt = datetime.fromisoformat(str(entry2["next_fire_at"]).replace("Z", "+00:00"))
    assert nxt > datetime.now(UTC)


def test_schedule_preserves_next_fire_on_upsert() -> None:
    storage = _storage()
    work = WorkIntentStore(storage)
    sched = ScheduleRegistry(storage, work)
    sched.upsert("s1", flow_id="f", interval_seconds=60)
    entry = storage.get("palm:schedule:entry:s1")
    assert isinstance(entry, dict)
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    entry["next_fire_at"] = future
    storage.set("palm:schedule:entry:s1", entry)
    sched.upsert("s1", flow_id="f", interval_seconds=60, preserve_next_fire=True)
    entry2 = storage.get("palm:schedule:entry:s1")
    assert isinstance(entry2, dict)
    assert entry2["next_fire_at"] == future
