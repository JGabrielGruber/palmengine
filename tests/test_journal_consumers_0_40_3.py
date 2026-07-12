"""0.40.3 — named journal consumers + doctor control_plane."""

from __future__ import annotations

from palm.common.events.consumers import (
    DEFAULT_JOURNAL_CONSUMERS,
    JOURNAL_CONSUMER_PROJECTIONS,
    JOURNAL_CONSUMER_WEBHOOKS,
    consume_for_projections,
    consume_for_webhooks,
    journal_consumer_status,
    mark_work_drain_caught_up,
)
from palm.common.events.journal import EventJournal
from palm.common.runtimes.server.diagnostics import build_doctor_report
from palm.core.storage import StorageEngine


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

    seen_w: list[str] = []
    consume_for_webhooks(j, lambda e: seen_w.append(e.event_type), limit=10)
    assert "resource.changed" in seen_w
    assert j.get_consumer_offset(JOURNAL_CONSUMER_WEBHOOKS) > 0

    # projections start at 0 independently
    assert j.get_consumer_offset(JOURNAL_CONSUMER_PROJECTIONS) == 0
    seen_p: list[str] = []
    consume_for_projections(j, lambda e: seen_p.append(e.event_type), limit=10)
    assert len(seen_p) >= 2

    status = journal_consumer_status(j)
    assert status["latest_offset"] >= 3
    for name in DEFAULT_JOURNAL_CONSUMERS:
        assert name in status["consumers"]


def test_mark_work_drain_caught_up() -> None:
    j = _journal()
    j.append("resource.changed", {"a": 1})
    off = mark_work_drain_caught_up(j)
    assert off == j.latest_offset()
    assert journal_consumer_status(j)["consumers"]["work_drain"]["lag"] == 0


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
                "work_drain_running": False,
                "work_dropped_depth": 0,
                "outbox_pending": 0,
                "journal": {
                    "latest_offset": 2,
                    "consumers": {
                        "webhooks": {"offset": 0, "lag": 2},
                        "projections": {"offset": 0, "lag": 2},
                        "work_drain": {"offset": 2, "lag": 0},
                    },
                },
                "journal_consumers": list(DEFAULT_JOURNAL_CONSUMERS),
            }

    report = build_doctor_report(_RT(), control_plane=_Host().control_plane_status())
    assert "control_plane" in report
    assert report["control_plane"]["journal"]["latest_offset"] == 2
    # lag=2 is under soft threshold 100 — no journal lag issue
    assert report["status"] in ("ok", "degraded")
