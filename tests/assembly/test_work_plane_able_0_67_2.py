"""0.67.2 — work-plane able is drain membership; wait stays ready-only."""

from __future__ import annotations

from palm.core.structure import CAPABILITY_WORK_DRAIN, Observation, ObservationKind
from palm.core.work import WorkIntent
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.subsystems.planes.work.plane import WorkPlaneService
from tests.helpers.bound import bound_for_runtime


def test_embedded_ready_is_not_work_plane_able() -> None:
    """Default DNA is ready without work_drain. Drain able is false."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.admission.may_run_business is True
        assert rt.admission.has_capability(CAPABILITY_WORK_DRAIN) is False
        able = rt.install.able
        assert able is not None
        assert able() is False
        plane = rt.work_plane
        assert isinstance(plane, WorkPlaneService)
        assert plane.is_able() is False
        wait = rt.wait_plane
        assert wait is not None
        assert wait.is_able() is True
        plane._submit_flow = lambda *_a, **_k: None
        plane.enqueue(WorkIntent(kind="run_flow", target="no-organ"))
        assert plane.tick(limit=5) == 0
    finally:
        rt.stop()


def test_cli_work_plane_able_when_drain_installed() -> None:
    reset_system_log_for_tests()
    submitted: list[str] = []
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        assert rt.admission.may_run_business is True
        assert rt.admission.has_capability(CAPABILITY_WORK_DRAIN) is True
        able = rt.install.able
        assert able is not None
        assert able() is True
        plane = rt.work_plane
        assert plane is not None
        assert plane.is_able() is True
        wait = rt.wait_plane
        assert wait is not None
        assert wait.is_able() is True
        plane._submit_flow = lambda fid, _p: submitted.append(fid)
        plane.enqueue(WorkIntent(kind="run_flow", target="ok-flow"))
        assert plane.tick(limit=5) == 1
        assert submitted == ["ok-flow"]
    finally:
        rt.stop()


def test_truth_home_down_closes_work_and_wait() -> None:
    reset_system_log_for_tests()
    submitted: list[str] = []
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        plane = rt.work_plane
        assert plane is not None
        plane._submit_flow = lambda fid, _p: submitted.append(fid)
        plane.enqueue(WorkIntent(kind="run_flow", target="blocked-flow"))
        assert rt.structure is not None
        rt.structure.engine.observe(Observation(kind=ObservationKind.TRUTH_HOME_DOWN))
        assert rt.admission.may_run_business is False
        assert plane.is_able() is False
        wait = rt.wait_plane
        assert wait is not None
        assert wait.is_able() is False
        assert plane.tick(limit=10) == 0
        assert submitted == []

        rt.structure.engine.observe(Observation(kind=ObservationKind.TRUTH_HOME_UP))
        rt.structure.engine.tick()
        assert rt.admission.may_run_business is True
        assert rt.admission.has_capability(CAPABILITY_WORK_DRAIN) is True
        assert plane.is_able() is True
        assert wait.is_able() is True
        assert plane.tick(limit=10) == 1
        assert submitted == ["blocked-flow"]
    finally:
        rt.stop()
