"""0.66.1 — seat publishes installed names; product reads the gate."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import (
    CAPABILITY_OUTBOX,
    CAPABILITY_WORK_DRAIN,
    AdmissionSnapshot,
    StructurePhase,
    local_cli,
    local_embedded,
)
from palm.system.log import reset_system_log_for_tests
from palm.system.structure import (
    AdmissionRefusedError,
    CapabilitySeats,
    StructureSeat,
    coerce_admission_snapshot,
    require_business_admission,
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


def test_coerce_round_trips_capabilities() -> None:
    ready = AdmissionSnapshot(
        may_run_business=True,
        phase=StructurePhase.READY,
        capabilities=frozenset({CAPABILITY_WORK_DRAIN}),
    )
    assert coerce_admission_snapshot(ready) is ready
    duck = SimpleNamespace(
        may_run_business=True,
        phase=StructurePhase.READY,
        definition_id="local.cli",
        definition_version="1",
        capabilities=["work_drain", "outbox"],
    )
    coerced = coerce_admission_snapshot(duck)
    assert coerced is not None
    assert coerced.has_capability(CAPABILITY_WORK_DRAIN) is True
    assert coerced.has_capability(CAPABILITY_OUTBOX) is True


def test_coerce_defaults_missing_capabilities() -> None:
    duck = SimpleNamespace(
        may_run_business=True,
        phase=StructurePhase.READY,
        definition_id="test",
    )
    coerced = coerce_admission_snapshot(duck)
    assert coerced is not None
    assert coerced.capabilities == frozenset()
    assert coerced.has_capability("work_drain") is False


def test_require_still_fail_closes_on_ready_wall() -> None:
    closed = AdmissionSnapshot(
        may_run_business=False,
        phase=StructurePhase.BLOCKED,
        reasons=("test_closed",),
        capabilities=frozenset({CAPABILITY_WORK_DRAIN}),
    )
    with pytest.raises(AdmissionRefusedError):
        require_business_admission(closed)


def test_seat_publishes_installed_not_dna_list() -> None:
    seat = StructureSeat()
    seat.assemble(local_cli())
    assert seat.admission().has_capability(CAPABILITY_WORK_DRAIN) is False
    assert local_cli().has_capability(CAPABILITY_WORK_DRAIN) is True

    seat.materialize(
        CapabilitySeats(
            supervisor=SystemSupervisor(definitions=()),
            work_plane=_FakePlane(),
        )
    )
    snap = seat.admission()
    assert snap.has_capability(CAPABILITY_WORK_DRAIN) is True
    assert snap.has_capability(CAPABILITY_OUTBOX) is True
    assert snap.may_run_business is True


def test_seat_embedded_publishes_empty_installed() -> None:
    seat = StructureSeat()
    seat.assemble(local_embedded())
    seat.materialize(
        CapabilitySeats(
            supervisor=SystemSupervisor(definitions=()),
            work_plane=_FakePlane(),
        )
    )
    assert seat.admission().capabilities == frozenset()
    assert seat.admission().has_capability(CAPABILITY_WORK_DRAIN) is False


def test_product_reads_has_capability_on_published_gate() -> None:
    """Business reads host.admission — not runtime.structure."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        gate = host.admission
        assert gate.has_capability("work_drain") is True
        snap = coerce_admission_snapshot(gate)
        assert snap is not None
        assert snap.has_capability("work_drain") is True
        assert "work_drain" in snap.to_dict()["capabilities"]
    finally:
        host.shutdown()
