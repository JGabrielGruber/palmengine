"""0.55.6 — wait interest rehydrate + double-event idempotency."""

from __future__ import annotations

import palm.providers  # noqa: F401
from palm.common.persistence.state_snapshot import snapshot_state, state_from_snapshot
from palm.system.subsystems.planes.wait.index import WaitOwnerIndex
from palm.system.subsystems.planes.wait.matcher import WaitMatcher
from palm.core import StorageEngine
from palm.core.orchestration import Job, JobStatus
from palm.core.wait import (
    STATE_KEY_WAIT_INTERESTS,
    has_open_waits,
    list_wait_interests,
    make_job_wait,
    open_wait_on_job,
    rehydrate_wait_interests,
)
from palm.definitions import FlowDefinition, ResourceDefinition
from palm.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.storages import memory  # noqa: F401


def test_snapshot_roundtrip_preserves_wait_interest() -> None:
    job = Job(id="owner", executable=None)
    open_wait_on_job(
        job,
        make_job_wait("child-1", meta={"source": "nested_wizard", "step_slug": "spawn"}),
    )
    snap = snapshot_state(job.state)
    assert STATE_KEY_WAIT_INTERESTS in snap
    restored = state_from_snapshot(snap)
    interests = rehydrate_wait_interests(restored)
    assert len(interests) == 1
    assert interests[0].target_id == "child-1"
    assert interests[0].meta["source"] == "nested_wizard"


def test_rehydrate_prunes_corrupt_entries() -> None:
    job = Job(id="o", executable=None)
    job.state.set(
        STATE_KEY_WAIT_INTERESTS,
        [
            "bad",
            {"kind": "", "target_id": "x"},
            {"kind": "job", "target_id": "good", "meta": {"source": "t"}},
        ],
    )
    interests = rehydrate_wait_interests(job.state)
    assert len(interests) == 1
    assert interests[0].target_id == "good"
    raw = job.state.get(STATE_KEY_WAIT_INTERESTS)
    assert isinstance(raw, list) and len(raw) == 1


def test_double_event_id_is_idempotent() -> None:
    owner = Job(id="owner-d", executable=None)
    owner.status = JobStatus.WAITING_FOR_INPUT
    open_wait_on_job(owner, make_job_wait("child-d"))
    resumes: list[str] = []
    matcher = WaitMatcher(
        index=WaitOwnerIndex(),
        get_job={owner.id: owner}.get,
        list_jobs=lambda: [owner],
        resume_owner=lambda oid, _i, _s: resumes.append(oid),
    )
    d1 = matcher.handle_payload(
        "job.completed",
        {"job_id": "child-d", "status": "SUCCEEDED"},
        event_id="evt-1",
    )
    d2 = matcher.handle_payload(
        "job.completed",
        {"job_id": "child-d", "status": "SUCCEEDED"},
        event_id="evt-1",
    )
    assert len(d1) == 1
    assert d2 == []
    assert resumes == ["owner-d"]


def test_twin_event_types_do_not_double_resume() -> None:
    """job.completed then flow.session.succeeded for same child → one resume."""
    owner = Job(id="owner-t", executable=None)
    owner.status = JobStatus.WAITING_FOR_INPUT
    open_wait_on_job(owner, make_job_wait("child-t"))
    resumes: list[str] = []
    matcher = WaitMatcher(
        get_job={owner.id: owner}.get,
        list_jobs=lambda: [owner],
        resume_owner=lambda oid, _i, _s: resumes.append(oid),
    )
    matcher.handle_payload(
        "job.completed",
        {"job_id": "child-t", "status": "SUCCEEDED"},
        event_id="a",
    )
    # Interest already closed; also acted_key guards if interest re-opened wrongly.
    matcher.handle_payload(
        "flow.session.succeeded",
        {"job_id": "child-t", "status": "SUCCEEDED"},
        event_id="b",
    )
    assert resumes == ["owner-t"]
    assert not has_open_waits(owner.state)


def _nested_flows() -> tuple[FlowDefinition, FlowDefinition, ResourceDefinition]:
    child = FlowDefinition(
        id="flow-child-556",
        name="child-556",
        pattern="wizard",
        options={"steps": [{"slug": "q", "prompt": "Child?"}]},
    )
    parent = FlowDefinition(
        id="flow-parent-556",
        name="parent-556",
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "spawn",
                    "step_kind": "resource",
                    "resource_ref": "submit-child-556",
                    "output_key": "child_job",
                },
            ],
        },
    )
    resource = ResourceDefinition(
        id="res-submit-556",
        name="submit-child-556",
        provider="palm",
        action="submit_flow",
        resource_id="flow:child-556",
        params={
            "wait": True,
            "wait_mode": "until_input",
            "timeout_seconds": 5,
        },
    )
    return child, parent, resource


def test_nested_mid_wait_survives_runtime_restart() -> None:
    """Park parent mid-child-wait, restart runtime, rehydrate interest, complete."""
    from palm.patterns.wizard.bindings.resource.nested_park import nested_park_interest

    storage = StorageEngine()
    storage.initialize(backend="memory")
    child_def, parent_def, res_def = _nested_flows()

    rt1 = EmbeddedRuntime(storage=storage)
    rt1.start()
    try:
        rt1.repository.save_flow(child_def)
        rt1.repository.save_flow(parent_def)
        rt1.repository.save_resource(res_def)

        parent_job = rt1.submit_flow("parent-556")
        rt1.wait_until_idle(timeout=5)
        assert parent_job.status == JobStatus.WAITING_FOR_INPUT
        assert has_open_waits(parent_job.state)

        park = nested_park_interest(parent_job.state)
        assert park is not None
        child_job_id = str(park.target_id)
        child_job = rt1.get_job(child_job_id)
        parent_instance_id = str(parent_job.metadata["instance_id"])
        child_instance_id = str(child_job.metadata["instance_id"])

        interests = list_wait_interests(parent_job.state)
        assert interests[0].target_id == child_job_id

        rt1.executor.persist_job(parent_job)
        rt1.executor.persist_job(child_job)
    finally:
        rt1.stop()

    rt2 = EmbeddedRuntime(storage=storage)
    rt2.start()
    try:
        resumed_parent = rt2.resume_process(parent_instance_id)
        assert resumed_parent.status == JobStatus.WAITING_FOR_INPUT
        assert has_open_waits(resumed_parent.state)
        rehydrated = list_wait_interests(resumed_parent.state)
        assert len(rehydrated) == 1
        assert rehydrated[0].target_id == child_job_id
        assert rehydrated[0].meta.get("source") == "nested_wizard"

        resumed_child = rt2.resume_process(child_instance_id)
        assert resumed_child.status == JobStatus.WAITING_FOR_INPUT

        rt2.provide_input(resumed_child.id, "after restart")
        rt2.wait_until_idle(timeout=5)

        child_done = rt2.get_job(resumed_child.id)
        parent_done = rt2.get_job(resumed_parent.id)
        assert child_done.status == JobStatus.SUCCEEDED
        assert parent_done.status == JobStatus.SUCCEEDED
        assert not has_open_waits(parent_done.state)
        assert nested_park_interest(parent_done.state) is None
    finally:
        rt2.stop()
        storage.shutdown()
        clear_palm_runtime()
