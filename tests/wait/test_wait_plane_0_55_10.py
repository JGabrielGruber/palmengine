"""0.55.10 — WaitPlaneService continue plane."""

from __future__ import annotations

from palm.core.event import EventEngine
from palm.core.orchestration import Job, JobStatus
from palm.core.wait import has_open_waits, make_job_wait
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from bundles.standard.runtimes.embedded import EmbeddedRuntime
from palm.system.subsystems.planes.wait import WaitPlaneService


def test_wait_plane_attach_and_resume() -> None:
    engine = EventEngine()
    engine.initialize()
    owner = Job(id="owner-plane", executable=None)
    owner.status = JobStatus.WAITING_FOR_INPUT

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
            pass

    class _Rt:
        event = engine
        orchestration = _Orch()

    plane = WaitPlaneService()
    plane.open_on_job(owner, make_job_wait("child-p"))
    rt = _Rt()
    # Unit mechanics: force able (0.63.26 default fail closed).
    plane.attach(
        orchestration=rt.orchestration, event=rt.event, able=lambda: True
    )
    assert plane.matcher is not None
    plane.handle_payload(
        "job.completed",
        {"job_id": "child-p", "status": "SUCCEEDED"},
        event_id="e1",
    )
    assert owner.status == JobStatus.RUNNING
    assert not has_open_waits(owner.state)
    plane.detach()


def test_embedded_runtime_exposes_wait_plane() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        assert rt.wait_plane is not None
        assert rt.wait_matcher is not None
        assert rt.wait_plane.matcher is rt.wait_matcher
        snap = rt.wait_plane.doctor_snapshot()
        assert snap["wait_plane_attached"] is True
        assert "continue" in snap["verbs"]
    finally:
        rt.stop()
        clear_palm_runtime()


def test_install_wait_plane_attaches() -> None:
    from palm.system.interfaces.install import SystemInstall
    from palm.system.subsystems.planes.hub import SystemPlanes
    from palm.system.subsystems.planes.install_access import require_system_install

    engine = EventEngine()
    engine.initialize()

    class _Orch:
        def get_job(self, job_id: str) -> None:
            return None

        @property
        def jobs(self) -> dict[str, Job]:
            return {}

        def resume_job(self, job_id: str) -> None:
            pass

        def apply_result(self, job: Job, result: object) -> None:
            pass

    class _Rt:
        def __init__(self) -> None:
            self.event = engine
            self.orchestration = _Orch()
            self._planes = None
            self._install = SystemInstall()

        @property
        def install(self) -> SystemInstall:
            return self._install

        def bind_system_install(self) -> SystemInstall:
            return self._install.bind(
                orchestration=self.orchestration,
                event=self.event,
                submit=lambda *a, **k: None,
                able=lambda: True,
            )

    rt = _Rt()
    board = require_system_install(rt)
    planes = SystemPlanes.ensure_on(rt)
    plane = planes.install_wait(board)
    assert plane.matcher is not None
    plane.detach()


def test_doctor_uses_wait_plane_snapshot() -> None:
    from plugins.kits.server.diagnostics import build_doctor_report

    rt = EmbeddedRuntime()
    rt.start()
    try:
        owner = Job(id="doc-owner", executable=None)
        owner.status = JobStatus.WAITING_FOR_INPUT
        assert rt.wait_plane is not None
        rt.wait_plane.open_on_job(owner, make_job_wait("child-doc"))
        snap = rt.wait_plane.doctor_snapshot([owner])
        assert snap["wait_plane_attached"] is True
        assert snap["open_wait_owners"] == 1
        assert snap["wait_kinds"].get("job") == 1

        report = build_doctor_report(rt)
        assert report["reactive_interests"]["wait_matcher_wired"] is True
        assert report["reactive_interests"].get("wait_plane_attached") is True
    finally:
        rt.stop()
        clear_palm_runtime()
