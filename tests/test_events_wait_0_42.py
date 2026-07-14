"""0.42 — event wait helpers + journal-assisted remote wait path."""

from __future__ import annotations

from palm.common.events.catalog import is_public_event_type
from palm.providers.palm.events_client import PalmEventsClient, event_mentions_job


def test_event_mentions_job() -> None:
    assert event_mentions_job(
        {"type": "job.completed", "payload": {"job_id": "job-1"}},
        "job-1",
    )
    assert not event_mentions_job(
        {"type": "job.completed", "payload": {"job_id": "job-2"}},
        "job-1",
    )


def test_wait_for_job_matches_payload() -> None:
    client = PalmEventsClient("http://127.0.0.1:1")
    # inject without network
    events = [
        {
            "offset": 1,
            "type": "resource.changed",
            "payload": {"resource_ref": "x", "action": "put"},
        },
        {
            "offset": 2,
            "type": "job.completed",
            "payload": {"job_id": "job-abc", "status": "SUCCEEDED"},
        },
    ]
    idx = {"i": 0}

    def fake_poll(**kwargs):
        del kwargs
        i = idx["i"]
        if i >= len(events):
            return []
        idx["i"] = i + 1
        client._offset = events[i]["offset"]
        return [events[i]]

    client.poll = fake_poll  # type: ignore[method-assign]
    hit = client.wait_for_job("job-abc", timeout=2.0, poll_interval=0.01)
    assert hit["type"] == "job.completed"
    assert hit["payload"]["job_id"] == "job-abc"


def test_wait_for_resource_action_filter() -> None:
    client = PalmEventsClient("http://127.0.0.1:1")
    batch = [
        {
            "offset": 1,
            "type": "resource.changed",
            "payload": {"resource_ref": "palm-todos", "action": "get"},
        },
        {
            "offset": 2,
            "type": "resource.changed",
            "payload": {"resource_ref": "palm-todos", "action": "put"},
        },
    ]
    idx = {"i": 0}

    def fake_poll(**kwargs):
        del kwargs
        i = idx["i"]
        if i >= len(batch):
            return []
        idx["i"] = i + 1
        return [batch[i]]

    client.poll = fake_poll  # type: ignore[method-assign]
    hit = client.wait_for_resource(
        "palm-todos",
        action="put",
        timeout=2.0,
        poll_interval=0.01,
    )
    assert hit["payload"]["action"] == "put"
    assert is_public_event_type(hit["type"])
