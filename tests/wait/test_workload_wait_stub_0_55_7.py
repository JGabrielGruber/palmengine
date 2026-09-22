"""0.55.7 — workload wait kind stub: open wait → emit ready/fail → matcher."""

from __future__ import annotations

from palm.system.subsystems.planes.wait.matcher import WaitMatcher
from palm.system.subsystems.planes.wait.policy import ACTION_FAIL_OWNER, ACTION_RESUME_OWNER
from palm.system.subsystems.planes.wait.present import waiting_on_from_job
from palm.system.subsystems.planes.wait.workload_stub import (
    emit_workload_failed,
    emit_workload_ready,
    open_workload_wait,
)
from palm.core.event import EventEngine
from palm.core.orchestration import Job, JobStatus
from palm.core.wait import (
    ON_TARGET_FAILED_LEAVE,
    WAIT_KIND_WORKLOAD,
    WaitInterest,
    WaitPolicy,
    has_open_waits,
    open_wait_on_job,
)
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from bundles.standard.runtimes.embedded import EmbeddedRuntime


def test_open_workload_wait_kind() -> None:
    job = Job(id="owner-wl", executable=None)
    interest = open_workload_wait(job, "wl-1", meta={"step_slug": "run_hermetic"})
    assert interest.kind == WAIT_KIND_WORKLOAD
    assert interest.target_id == "wl-1"
    assert interest.meta["source"] == "workload_stub"
    rows = waiting_on_from_job(job)
    assert rows[0]["kind"] == "workload"
    assert rows[0]["target_id"] == "wl-1"


def test_emit_ready_resumes_owner_via_matcher() -> None:
    engine = EventEngine()
    engine.initialize()
    owner = Job(id="owner-ready", executable=None)
    owner.status = JobStatus.WAITING_FOR_INPUT
    open_workload_wait(owner, "wl-ready")

    resumes: list[str] = []
    fails: list[str] = []
    matcher = WaitMatcher(
        get_job={owner.id: owner}.get,
        list_jobs=lambda: [owner],
        resume_owner=lambda oid, _i, _s: resumes.append(oid),
        fail_owner=lambda oid, _i, _s: fails.append(oid),
    )
    matcher.attach_events(engine)

    emit_workload_ready(engine, "wl-ready")
    assert resumes == ["owner-ready"]
    assert fails == []
    assert not has_open_waits(owner.state)
    matcher.detach_events()


def test_emit_failed_fails_owner_by_default() -> None:
    engine = EventEngine()
    engine.initialize()
    owner = Job(id="owner-fail", executable=None)
    owner.status = JobStatus.WAITING_FOR_INPUT
    open_workload_wait(owner, "wl-bad")

    fails: list[tuple[str, str]] = []
    matcher = WaitMatcher(
        get_job={owner.id: owner}.get,
        list_jobs=lambda: [owner],
        fail_owner=lambda oid, _i, sig: fails.append((oid, sig.outcome)),
    )
    matcher.attach_events(engine)
    emit_workload_failed(engine, "wl-bad", error="boom")
    assert fails == [("owner-fail", "failed")]
    assert not has_open_waits(owner.state)
    matcher.detach_events()


def test_emit_failed_leave_policy_keeps_interest() -> None:
    engine = EventEngine()
    engine.initialize()
    owner = Job(id="owner-leave", executable=None)
    owner.status = JobStatus.WAITING_FOR_INPUT
    open_wait_on_job(
        owner,
        WaitInterest(
            kind=WAIT_KIND_WORKLOAD,
            target_id="wl-leave",
            policy=WaitPolicy(on_target_failed=ON_TARGET_FAILED_LEAVE),
            meta={"source": "workload_stub"},
        ),
    )
    fails: list[str] = []
    matcher = WaitMatcher(
        get_job={owner.id: owner}.get,
        list_jobs=lambda: [owner],
        fail_owner=lambda oid, _i, _s: fails.append(oid),
    )
    matcher.attach_events(engine)
    emit_workload_failed(engine, "wl-leave")
    assert fails == []
    assert has_open_waits(owner.state)
    matcher.detach_events()


def test_runtime_event_bus_emits_workload_ready() -> None:
    """Stub events publish on the same runtime.event bus the matcher uses."""
    rt = EmbeddedRuntime()
    rt.start()
    try:
        assert rt.wait_matcher is not None
        seen: list[str] = []
        rt.event.subscribe("workload.ready", lambda e: seen.append(e.type))
        emit_workload_ready(rt.event, "wl-bus-1")
        assert seen == ["workload.ready"]

        # Full unpark path on the runtime bus (sidecar owner, not orch registry).
        owner = Job(id="rt-owner-wl", executable=None)
        owner.status = JobStatus.WAITING_FOR_INPUT
        open_workload_wait(owner, "wl-rt-1")
        resumes: list[str] = []
        # Temporary list_jobs/get_job for this owner on the live matcher.
        matcher = rt.wait_matcher
        prev_get, prev_list = matcher.get_job, matcher.list_jobs
        jobs = {owner.id: owner}
        matcher.get_job = jobs.get
        matcher.list_jobs = lambda: list(jobs.values())
        matcher.resume_owner = lambda oid, _i, _s: resumes.append(oid)
        try:
            emit_workload_ready(rt.event, "wl-rt-1")
            assert resumes == ["rt-owner-wl"]
            assert not has_open_waits(owner.state)
        finally:
            matcher.get_job = prev_get
            matcher.list_jobs = prev_list
    finally:
        rt.stop()
        clear_palm_runtime()


def test_handle_payload_actions_align() -> None:
    owner = Job(id="o", executable=None)
    open_workload_wait(owner, "w")
    matcher = WaitMatcher(get_job={owner.id: owner}.get, list_jobs=lambda: [owner])
    disps = matcher.handle_payload("workload.ready", {"workload_id": "w"})
    assert disps[0].action == ACTION_RESUME_OWNER

    owner2 = Job(id="o2", executable=None)
    open_workload_wait(owner2, "w2")
    matcher2 = WaitMatcher(get_job={owner2.id: owner2}.get, list_jobs=lambda: [owner2])
    disps2 = matcher2.handle_payload("workload.failed", {"workload_id": "w2"})
    assert disps2[0].action == ACTION_FAIL_OWNER
