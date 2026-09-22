"""0.67.3 — host start_ports.able is drain; wait stays ready."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.host.workplane.start_ports import product_start_ports
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import (
    CAPABILITY_WORK_DRAIN,
    AdmissionSnapshot,
    Observation,
    ObservationKind,
    StructurePhase,
)
from palm.system.log import reset_system_log_for_tests
from palm.system.subsystems.planes.work.plane import WorkPlaneService


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def _ports(
    *,
    started: bool,
    snap: AdmissionSnapshot,
) -> tuple[object, object, object]:
    return product_start_ports(
        execution=object(),
        session=None,
        started=lambda: started,
        admission=lambda: snap,
    )


def test_started_without_drain_is_not_work_able() -> None:
    """Host able is membership, not host._started."""
    ready = AdmissionSnapshot(
        may_run_business=True,
        phase=StructurePhase.READY,
        definition_id="local.embedded",
    )
    _submit, able, admission_able = _ports(started=True, snap=ready)
    assert able() is False
    assert admission_able() is True


def test_started_with_drain_is_work_able() -> None:
    snap = AdmissionSnapshot(
        may_run_business=True,
        phase=StructurePhase.READY,
        capabilities=frozenset({CAPABILITY_WORK_DRAIN}),
    )
    _submit, able, admission_able = _ports(started=True, snap=snap)
    assert able() is True
    assert admission_able() is True


def test_not_started_closes_work_and_wait() -> None:
    snap = AdmissionSnapshot(
        may_run_business=True,
        phase=StructurePhase.READY,
        capabilities=frozenset({CAPABILITY_WORK_DRAIN}),
    )
    _submit, able, admission_able = _ports(started=False, snap=snap)
    assert able() is False
    assert admission_able() is False


def test_closed_organism_closes_both_even_when_drain_listed() -> None:
    snap = AdmissionSnapshot(
        may_run_business=False,
        phase=StructurePhase.BLOCKED,
        reasons=("truth_home_down",),
        capabilities=frozenset({CAPABILITY_WORK_DRAIN}),
    )
    _submit, able, admission_able = _ports(started=True, snap=snap)
    assert able() is False
    assert admission_able() is False


def test_host_safe_wait_able_without_drain() -> None:
    """Continue is ready-only. Host override must not share drain onto wait."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert host.admission.may_run_business is True
        assert host.admission.has_capability(CAPABILITY_WORK_DRAIN) is False
        rt = host.runtime()
        able = rt.install.able
        assert able is not None
        assert able() is False
        plane = rt.work_plane
        assert isinstance(plane, WorkPlaneService)
        assert plane.is_able() is False
        wait = rt.wait_plane
        assert wait is not None
        assert wait.is_able() is True
    finally:
        host.shutdown()


def test_host_cli_work_and_wait_able() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        assert host.admission.may_run_business is True
        assert host.admission.has_capability(CAPABILITY_WORK_DRAIN) is True
        rt = host.runtime()
        able = rt.install.able
        assert able is not None
        assert able() is True
        assert rt.work_plane is not None
        assert rt.work_plane.is_able() is True
        wait = rt.wait_plane
        assert wait is not None
        assert wait.is_able() is True
    finally:
        host.shutdown()


def test_host_truth_home_down_closes_work_and_wait() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        rt = host.runtime()
        plane = rt.work_plane
        wait = rt.wait_plane
        assert plane is not None
        assert wait is not None
        assert rt.structure is not None
        rt.structure.engine.observe(Observation(kind=ObservationKind.TRUTH_HOME_DOWN))
        assert host.admission.may_run_business is False
        assert plane.is_able() is False
        assert wait.is_able() is False
        rt.structure.engine.observe(Observation(kind=ObservationKind.TRUTH_HOME_UP))
        rt.structure.engine.tick()
        assert host.admission.may_run_business is True
        assert plane.is_able() is True
        assert wait.is_able() is True
    finally:
        host.shutdown()
