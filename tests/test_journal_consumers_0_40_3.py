"""0.40.3 — named journal consumers + doctor control_plane."""

from __future__ import annotations

from palm.common.events.consumers import (
    DEFAULT_JOURNAL_CONSUMERS,
    journal_consumer_status,
)
from palm.common.events.journal import EventJournal
from palm.core.storage import StorageEngine
from plugins.kits.server.diagnostics import build_doctor_report


def _journal() -> EventJournal:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return EventJournal(s)


def test_named_consumers_independent_offsets() -> None:
    j = _journal()
    j.append("resource.changed", {"resource_ref": "palm-todos", "action": "put"})
    j.append("job.completed", {"job_id": "j1"})
    j.append("resource.changed", {"resource_ref": "x", "action": "put"})

    batch = j.consume("c1", limit=10, auto_commit=True)
    assert any(e.event_type == "resource.changed" for e in batch)
    assert j.get_consumer_offset("c1") > 0

    # a second consumer name does not share the offset
    assert j.get_consumer_offset("ops_redrive") == 0

    status = journal_consumer_status(j, consumers=["c1", "ops_redrive"])
    assert status["latest_offset"] >= 3
    assert "c1" in status["consumers"]
    assert "ops_redrive" in status["consumers"]
    assert status["consumers"]["c1"]["lag"] == 0
    assert "work_drain" not in status["consumers"]
    assert "work_drain" not in DEFAULT_JOURNAL_CONSUMERS


def test_doctor_embeds_control_plane() -> None:
    class _RT:
        runtime_name = "test"
        storage = None
        orchestration = None
        repository = None
        auth_enforce = False

    class _Host:
        def control_plane_status(self) -> dict:
            return {
                "work_pending": 0,
                "start_plane_running": False,
                "work_dropped_depth": 0,
                "outbox_pending": 0,
                "journal": {
                    "latest_offset": 2,
                    "consumers": {},
                },
                "journal_consumers": list(DEFAULT_JOURNAL_CONSUMERS),
            }

    report = build_doctor_report(_RT(), control_plane=_Host().control_plane_status())
    assert "control_plane" in report
    assert report["control_plane"]["journal"]["latest_offset"] == 2
    assert "work_drain" not in report["control_plane"]["journal"]["consumers"]
    assert report["status"] in ("ok", "degraded")
