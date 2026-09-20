"""compensation leftover — one attach, one host object, not a loop (0.67.12)."""

from __future__ import annotations

from palm.app.host.application_host import ApplicationHost
from palm.app.host.boot.modes import BootMode
from palm.app.settings import PalmSettings
from palm.common.compensation.events import CompensationEventType, CompensationTrigger
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.structure import (
    CAPABILITY_COMPENSATION,
    LOCAL_CLI_ID,
    LOCAL_EMBEDDED_ID,
    local_cli,
    local_embedded,
)
from palm.system.boot.context import BootContext
from palm.system.interfaces.install import SystemInstall
from palm.system.log import reset_system_log_for_tests
from palm.system.structure import CapabilitySeats, apply_local_capabilities
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES, admission_inventory
from palm.system.structure.phase_assemble import run as assemble_run
from palm.system.subsystems.supervisor import SystemSupervisor
from palm.system.subsystems.supervisor.definition import DEFAULT_CONTINUOUS_DEFINITIONS
from tests.helpers.event_plane import runtime_event_engine


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def _compensation_seats() -> CapabilitySeats:
    event = EventEngine()
    event.initialize()
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    board = SystemInstall()
    board.bind(event=event, storage=storage)
    return CapabilitySeats(
        install=board, event=event, storage=storage, supervisor=SystemSupervisor(definitions=())
    )


def test_compensation_is_not_a_supervisor_loop() -> None:
    seats = _compensation_seats()
    apply_local_capabilities(local_cli(), seats)
    assert seats.install.compensation is not None
    assert "compensation" not in seats.supervisor.names()
    assert "compensation" not in {d.name for d in DEFAULT_CONTINUOUS_DEFINITIONS}


def test_drop_on_omit_unsubscribes_without_a_service() -> None:
    seats = _compensation_seats()
    apply_local_capabilities(local_cli(), seats)
    bag = seats.install.compensation
    skipped: list[str] = []
    seats.event.subscribe(CompensationEventType.SKIPPED, lambda e: skipped.append(e.type))
    seats.event.emit(CompensationTrigger.COMMIT_FAILED, hook="ghost-before")
    before = len(skipped)
    assert before >= 1

    dropped = apply_local_capabilities(local_embedded(), seats)
    assert CAPABILITY_COMPENSATION not in dropped
    assert seats.install.compensation is None
    assert "compensation" not in seats.supervisor.names()
    seats.event.emit(CompensationTrigger.COMMIT_FAILED, hook="ghost-after")
    assert len(skipped) == before
    assert bag is not seats.install.compensation


class _LeanShell:
    def __init__(self) -> None:
        self.structure = None
        self.install = None
        self.supervisor = None
        self.workload = None


def test_phase_assemble_seats_compensation_on_install_not_supervisor() -> None:
    reset_system_log_for_tests()
    event = EventEngine()
    event.initialize()
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    board = SystemInstall()
    board.bind(event=event, storage=storage)
    supervisor = SystemSupervisor(definitions=())
    ctx = BootContext(
        schedule="system",
        shell=_LeanShell(),
        install=board,
        supervisor=supervisor,
        event=event,
        storage=storage,
    )
    assemble_run(ctx, {"structure_definition_id": LOCAL_CLI_ID})
    assert board.compensation is not None
    assert "compensation" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_COMPENSATION in ctx.structure.materialized_capabilities

    assemble_run(ctx, {"structure_definition_id": LOCAL_EMBEDDED_ID})
    assert board.compensation is None
    assert CAPABILITY_COMPENSATION not in ctx.structure.materialized_capabilities


def test_cli_host_compensation_is_one_object_on_the_runtime_bus() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        rt = host.runtime()
        assert host.admission.has_capability(CAPABILITY_COMPENSATION)
        assert host._recovery.compensation is not None
        assert rt.install.compensation is not None
        assert host._recovery.compensation is rt.install.compensation
        assert "compensation" not in rt.supervisor.names()

        skipped: list[str] = []
        runtime_event_engine(host).subscribe(
            CompensationEventType.SKIPPED, lambda e: skipped.append(e.type)
        )
        before = len(skipped)
        runtime_event_engine(host).emit(CompensationTrigger.COMMIT_FAILED, hook="ghost-runtime")
        after_runtime = len(skipped)
        assert after_runtime >= before + 1

        host.event.emit(CompensationTrigger.COMMIT_FAILED, hook="ghost-host")
        assert len(skipped) == after_runtime
    finally:
        host.shutdown()


def test_embedded_host_still_omits_compensation() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert not host.admission.has_capability(CAPABILITY_COMPENSATION)
        assert host._recovery.compensation is None
        rt = host.runtime()
        assert rt.install.compensation is None
        assert rt.supervisor is None or "compensation" not in rt.supervisor.names()
    finally:
        host.shutdown()


def test_inventory_compensation_leftover_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "structure.compensation_one_organ" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["structure.compensation_composition_king"] == "paid_0_67_11"
    assert pretenders["structure.compensation_supervisor_costume"] == "paid_0_67_12"
    assert admission_inventory()["gated_count"] >= 1
