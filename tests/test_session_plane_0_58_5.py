"""0.58.5 — Session wait / inspect journey view (no private resume)."""

from __future__ import annotations

from palm.definitions import FlowDefinition
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from bundles.standard.runtimes.embedded import EmbeddedRuntime
from palm.system.subsystems.planes.session import SessionNotFoundError, SessionPlaneService
from palm.core.storage import StorageEngine
import pytest


def test_inspect_empty_session() -> None:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    plane = SessionPlaneService(storage=s)
    rec = plane.open(session_id="sess-empty")
    view = plane.inspect(rec.session_id)
    assert view["kind"] == "session_inspect"
    assert view["session_id"] == "sess-empty"
    assert view["instance_ids"] == []
    assert view["waiting_on"] == []
    assert view["counts"]["instances"] == 0
    assert "wait plane" in view["note"].lower() or "inspect only" in view["note"].lower()
    assert plane.list_waiting(rec.session_id) == []


def test_inspect_unknown_session() -> None:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    plane = SessionPlaneService(storage=s)
    with pytest.raises(SessionNotFoundError):
        plane.inspect("sess-missing")


def test_embedded_inspect_session_with_instance_and_waits() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        plane = rt.session_plane
        assert plane is not None
        sess = plane.bind(surface="test").session_id
        flow = FlowDefinition(
            name="inspect_demo",
            pattern="wizard",
            options={
                "steps": [
                    {"slug": "ask", "title": "Ask", "prompt": "What?"},
                ]
            },
        )
        job = rt.submit_flow(flow, metadata={"session_id": sess})
        iid = str(job.metadata["instance_id"])

        view = plane.inspect(sess)
        assert view["session_id"] == sess
        assert iid in view["instance_ids"]
        assert any(r["instance_id"] == iid for r in view["instances"])
        row = next(r for r in view["instances"] if r["instance_id"] == iid)
        assert row.get("job_id") == job.id
        assert row.get("status") is not None
        # Journey lists the instance; open waits when interests exist (not always on wizard).
        assert isinstance(view["waiting_on"], list)
        assert view["counts"]["instances"] >= 1

        waits = plane.list_waiting(sess)
        assert isinstance(waits, list)
        for w in waits:
            assert w.get("session_id") == sess
            assert w.get("instance_id") == iid

        snap = plane.doctor_snapshot()
        assert "inspect" in snap["verbs"]
        assert "list_waiting" in snap["verbs"]
    finally:
        rt.stop()
        clear_palm_runtime()


def test_inspect_does_not_resume() -> None:
    """Sanity: inspect is read-only relative to job status."""
    rt = EmbeddedRuntime()
    rt.start()
    try:
        plane = rt.session_plane
        assert plane is not None
        sess = plane.bind().session_id
        flow = FlowDefinition(
            name="no_resume",
            pattern="wizard",
            options={"steps": [{"slug": "a", "title": "A", "prompt": "?"}]},
        )
        job = rt.submit_flow(flow, metadata={"session_id": sess})
        status_before = job.status
        plane.inspect(sess)
        plane.list_waiting(sess)
        again = rt.get_job(job.id)
        assert again.status == status_before
    finally:
        rt.stop()
        clear_palm_runtime()
