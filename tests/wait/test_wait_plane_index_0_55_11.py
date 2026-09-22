"""0.55.11 — continue plane open path + index discipline."""

from __future__ import annotations

import plugins.providers  # noqa: F401
from palm.system.subsystems.planes.wait import WaitPlaneService
from palm.core.orchestration import Job, JobStatus
from palm.core.wait import WAIT_KIND_JOB, has_open_waits, list_wait_interests, make_job_wait
from palm.definitions import FlowDefinition, ResourceDefinition
from plugins.providers.palm.bindings.runtimes.wiring import bind_palm_runtime, clear_palm_runtime
from bundles.standard.runtimes.embedded import EmbeddedRuntime


def test_open_on_job_registers_index() -> None:
    plane = WaitPlaneService()
    owner = Job(id="idx-owner", executable=None)
    plane.open_on_job(owner, make_job_wait("child-idx"))
    owners = plane.index.owners_for(kind=WAIT_KIND_JOB, target_id="child-idx")
    assert "idx-owner" in owners
    plane.close_on_job(owner, kind=WAIT_KIND_JOB, target_id="child-idx")
    assert len(plane.index.owners_for(kind=WAIT_KIND_JOB, target_id="child-idx")) == 0
    assert not has_open_waits(owner.state)


def test_rebuild_index_from_live_jobs() -> None:
    plane = WaitPlaneService()
    owner = Job(id="rebuild-o", executable=None)
    # State-only open (no plane) then rebuild as if attach found live jobs.
    from palm.core.wait import open_wait_on_job

    open_wait_on_job(owner, make_job_wait("c-rebuild"))

    class _Orch:
        @property
        def jobs(self) -> dict[str, Job]:
            return {owner.id: owner}

        def get_job(self, job_id: str) -> Job | None:
            return owner if job_id == owner.id else None

        def resume_job(self, job_id: str) -> None:
            pass

        def apply_result(self, job: Job, result: object) -> None:
            pass

    class _Rt:
        event = type("E", (), {"subscribe": lambda *a, **k: type("S", (), {"unsubscribe": lambda s: None})()})()
        orchestration = _Orch()

    rt = _Rt()
    plane.attach(orchestration=rt.orchestration, event=rt.event)
    assert "rebuild-o" in plane.index.owners_for(kind=WAIT_KIND_JOB, target_id="c-rebuild")
    plane.detach()
    assert len(plane.index) == 0


def test_nested_park_registers_on_bound_plane() -> None:
    """With palm runtime bound, set_child_wait indexes via WaitPlaneService."""
    child = FlowDefinition(
        id="c-idx",
        name="child-idx-flow",
        pattern="wizard",
        options={"steps": [{"slug": "q", "prompt": "?"}]},
    )
    parent = FlowDefinition(
        id="p-idx",
        name="parent-idx-flow",
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "spawn",
                    "step_kind": "resource",
                    "resource_ref": "sub-idx",
                    "output_key": "child_job",
                },
            ],
        },
    )
    resource = ResourceDefinition(
        id="r-idx",
        name="sub-idx",
        provider="palm",
        action="submit_flow",
        resource_id="flow:child-idx-flow",
        params={"wait": True, "wait_mode": "until_input", "timeout_seconds": 5},
    )

    rt = EmbeddedRuntime()
    rt.start()
    bind_palm_runtime(rt)
    try:
        rt.repository.save_flow(child)
        rt.repository.save_flow(parent)
        rt.repository.save_resource(resource)

        parent_job = rt.submit_flow("parent-idx-flow")
        rt.wait_until_idle(timeout=5)
        assert parent_job.status == JobStatus.WAITING_FOR_INPUT
        from plugins.patterns.wizard.bindings.resource.nested_park import nested_park_interest

        park = nested_park_interest(parent_job.state)
        assert park is not None
        child_id = str(park.target_id)

        assert rt.wait_plane is not None
        owners = rt.wait_plane.index.owners_for(kind=WAIT_KIND_JOB, target_id=child_id)
        assert parent_job.id in owners
        assert list_wait_interests(parent_job.state)[0].target_id == child_id
    finally:
        rt.stop()
        clear_palm_runtime()
