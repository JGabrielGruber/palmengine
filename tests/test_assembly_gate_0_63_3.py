"""0.63.3 — admission gate on work-plane business path that needs admission (fail closed)."""

from __future__ import annotations

from palm.core.structure import (
    CAPABILITY_WORK_DRAIN,
    Observation,
    ObservationKind,
    StructurePhase,
)
from palm.core.work import WorkIntent
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.subsystems.planes.work.plane import WorkPlaneService
from tests.helpers.bound import bound_for_runtime


def test_work_plane_tick_when_admission_ready() -> None:
    reset_system_log_for_tests()
    submitted: list[str] = []
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        assert rt.admission.may_run_business is True
        assert rt.admission.has_capability(CAPABILITY_WORK_DRAIN) is True
        plane = rt.work_plane
        assert isinstance(plane, WorkPlaneService)
        assert plane.is_able() is True
        plane._submit_flow = lambda fid, _p: submitted.append(fid)
        plane.enqueue(WorkIntent(kind="run_flow", target="ok-flow"))
        assert plane.tick(limit=5) == 1
        assert submitted == ["ok-flow"]
    finally:
        rt.stop()


def test_work_plane_fail_closed_when_assembly_skipped() -> None:
    """structure_skip → no admission → tick must not start business."""
    reset_system_log_for_tests()
    submitted: list[str] = []
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"), structure_skip=True)
    try:
        assert rt.admission.may_run_business is False
        assert rt.admission.phase is StructurePhase.EMPTY
        plane = rt.work_plane
        assert plane is not None
        assert plane.is_able() is False
        plane._submit_flow = lambda fid, _p: submitted.append(fid)
        intent_id = plane.enqueue(WorkIntent(kind="run_flow", target="should-wait"))
        assert intent_id  # enqueue still allowed (deferred)
        assert plane.tick(limit=10) == 0
        assert submitted == []
        assert plane.store.pending_count() >= 1
        st = plane.status()
        assert st["able"] is False
    finally:
        rt.stop()


def test_work_plane_fail_closed_when_truth_home_down() -> None:
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
        assert plane.tick(limit=10) == 0
        assert submitted == []

        rt.structure.engine.observe(Observation(kind=ObservationKind.TRUTH_HOME_UP))
        # Need a tick of the engine to leave BLOCKED → READY
        rt.structure.engine.tick()
        assert rt.admission.may_run_business is True
        assert plane.is_able() is True
        assert plane.tick(limit=10) == 1
        assert submitted == ["blocked-flow"]
    finally:
        rt.stop()


def test_install_able_matches_drain_not_ready() -> None:
    """0.67.2 — board able is work_drain membership, not may_run_business."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        able = rt.install.able
        assert able is not None
        assert rt.admission.may_run_business is True
        assert able() is rt.admission.has_capability(CAPABILITY_WORK_DRAIN)
        assert able() is False
    finally:
        rt.stop()
