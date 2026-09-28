"""0.63.26 — wait-plane continue resume is able-gated (admission fail closed)."""

from __future__ import annotations

from palm.core.event import EventEngine
from palm.core.orchestration import Job, JobStatus
from palm.core.wait import has_open_waits, make_job_wait
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure.errors import AdmissionRefusedError
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES
from palm.system.subsystems.planes.wait.plane import WaitPlaneService
from tests.helpers.bound import bound_for_runtime


def _orch_for(owner: Job) -> object:
    class _Orch:
        def get_job(self, job_id: str) -> Job | None:
            return owner if job_id == owner.id else None

        @property
        def jobs(self) -> dict[str, Job]:
            return {owner.id: owner}

        def resume_job(self, job_id: str) -> None:
            if job_id == owner.id:
                owner.status = JobStatus.RUNNING

        def apply_result(self, job: Job, result: object) -> None:
            status = getattr(result, "status", None)
            if status is not None:
                job.status = status
            err = getattr(result, "error", None)
            if err is not None:
                job.error = err

    return _Orch()


def test_wait_resume_default_able_fail_closed() -> None:
    engine = EventEngine()
    engine.initialize()
    owner = Job(id="owner-closed", executable=None)
    owner.status = JobStatus.WAITING_FOR_INPUT
    plane = WaitPlaneService()
    plane.open_on_job(owner, make_job_wait("child-c"))
    plane.attach(orchestration=_orch_for(owner), event=engine)  # able omit
    assert plane.is_able() is False
    plane.handle_payload(
        "job.completed",
        {"job_id": "child-c", "status": "SUCCEEDED"},
        event_id="e-closed",
    )
    assert owner.status == JobStatus.FAILED
    assert isinstance(getattr(owner, "error", None), AdmissionRefusedError)
    assert plane.doctor_snapshot()["refused_resumes"] >= 1
    plane.detach()


def test_wait_resume_when_able() -> None:
    engine = EventEngine()
    engine.initialize()
    owner = Job(id="owner-open", executable=None)
    owner.status = JobStatus.WAITING_FOR_INPUT
    plane = WaitPlaneService()
    plane.open_on_job(owner, make_job_wait("child-o"))
    plane.attach(orchestration=_orch_for(owner), event=engine, able=lambda: True)
    plane.handle_payload(
        "job.completed",
        {"job_id": "child-o", "status": "SUCCEEDED"},
        event_id="e-open",
    )
    assert owner.status == JobStatus.RUNNING
    assert not has_open_waits(owner.state)
    plane.detach()


def test_set_able_none_fails_closed() -> None:
    plane = WaitPlaneService()
    plane.set_able(lambda: True)
    assert plane.is_able() is True
    plane.set_able(None)
    assert plane.is_able() is False


def test_runtime_wait_plane_able_tracks_admission() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        assert rt.admission.may_run_business is False
        plane = rt.wait_plane
        assert plane is not None
        assert plane.is_able() is False
    finally:
        rt.stop()


def test_runtime_wait_plane_able_when_admitted() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.admission.may_run_business is True
        plane = rt.wait_plane
        assert plane is not None
        assert plane.is_able() is True
    finally:
        rt.stop()


def test_inventory_wait_able_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "wait_plane.able_resume" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["wait_plane.orch_resume_dig"] == "paid_0_63_26"
