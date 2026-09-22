"""0.67.1 — require_capability: ready then organ; drain-shaped caller."""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import (
    CAPABILITY_WORK_DRAIN,
    AdmissionSnapshot,
    StructurePhase,
    local_cli,
    local_embedded,
)
from palm.system.log import reset_system_log_for_tests
from palm.system.structure import (
    AdmissionRefusedError,
    CapabilityRefusedError,
    CapabilitySeats,
    StructureSeat,
    require_capability,
)
from palm.system.subsystems.supervisor import SystemSupervisor


class _FakePlane:
    def start_background(self) -> None:
        return None

    def stop_background(self) -> None:
        return None

    def status(self) -> dict[str, object]:
        return {"name": "work_drain", "running": False}


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def _drain_shaped(source: object) -> AdmissionSnapshot:
    """Drain-shaped act: require the organ. Ready is not membership."""
    return require_capability(source, CAPABILITY_WORK_DRAIN)


def test_ready_and_installed_returns_snapshot() -> None:
    ready = AdmissionSnapshot(
        may_run_business=True,
        phase=StructurePhase.READY,
        capabilities=frozenset({CAPABILITY_WORK_DRAIN}),
    )
    snap = require_capability(ready, CAPABILITY_WORK_DRAIN)
    assert snap is ready
    assert snap.has_capability(CAPABILITY_WORK_DRAIN) is True


def test_not_ready_is_admission_even_when_name_listed() -> None:
    closed = AdmissionSnapshot(
        may_run_business=False,
        phase=StructurePhase.BLOCKED,
        reasons=("test_closed",),
        capabilities=frozenset({CAPABILITY_WORK_DRAIN}),
    )
    with pytest.raises(AdmissionRefusedError):
        require_capability(closed, CAPABILITY_WORK_DRAIN)


def test_ready_without_organ_is_capability_refused() -> None:
    ready = AdmissionSnapshot(
        may_run_business=True,
        phase=StructurePhase.READY,
        definition_id="local.embedded",
    )
    with pytest.raises(CapabilityRefusedError) as caught:
        require_capability(ready, CAPABILITY_WORK_DRAIN)
    err = caught.value
    assert err.name == CAPABILITY_WORK_DRAIN
    assert err.snapshot is ready
    assert "work_drain" in str(err)


def test_missing_source_is_admission() -> None:
    with pytest.raises(AdmissionRefusedError):
        require_capability(None, CAPABILITY_WORK_DRAIN)


def test_seat_drain_shaped_requires_installed_not_ready() -> None:
    """Ready organism without the organ is not membership."""
    seat = StructureSeat()
    seat.assemble(local_embedded())
    seat.materialize(
        CapabilitySeats(
            supervisor=SystemSupervisor(definitions=()),
            work_plane=_FakePlane(),
        )
    )
    snap = seat.admission()
    assert snap.may_run_business is True
    assert snap.has_capability(CAPABILITY_WORK_DRAIN) is False
    with pytest.raises(CapabilityRefusedError):
        _drain_shaped(seat.admission)

    listed = StructureSeat()
    listed.assemble(local_cli())
    listed.materialize(
        CapabilitySeats(
            supervisor=SystemSupervisor(definitions=()),
            work_plane=_FakePlane(),
        )
    )
    got = _drain_shaped(listed.admission)
    assert got.has_capability(CAPABILITY_WORK_DRAIN) is True
    assert got.may_run_business is True


def test_drain_shaped_caller_uses_published_gate() -> None:
    """Drain-shaped caller reads the host gate — not runtime.structure."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        snap = _drain_shaped(host.admission)
        assert snap.has_capability(CAPABILITY_WORK_DRAIN) is True
    finally:
        host.shutdown()

    reset_system_log_for_tests()
    lean = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    lean.start()
    try:
        gate = lean.admission
        assert gate.may_run_business is True
        assert gate.has_capability(CAPABILITY_WORK_DRAIN) is False
        with pytest.raises(CapabilityRefusedError) as caught:
            _drain_shaped(gate)
        assert caught.value.name == CAPABILITY_WORK_DRAIN
    finally:
        lean.shutdown()
