"""journal leftover — one attach, one host object, not a loop (0.67.8)."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.structure import (
    CAPABILITY_JOURNAL,
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


def _journal_seats() -> CapabilitySeats:
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


def test_journal_is_not_a_supervisor_loop() -> None:
    seats = _journal_seats()
    apply_local_capabilities(local_cli(), seats)
    assert seats.install.event_journal is not None
    assert "journal" not in seats.supervisor.names()
    assert "journal" not in {d.name for d in DEFAULT_CONTINUOUS_DEFINITIONS}


def test_drop_on_omit_unsubscribes_without_a_service() -> None:
    seats = _journal_seats()
    apply_local_capabilities(local_cli(), seats)
    journal = seats.install.event_journal
    seats.event.emit("resource.changed", resource_ref="x", action="put")
    before = journal.latest_offset()
    assert before >= 1

    dropped = apply_local_capabilities(local_embedded(), seats)
    assert CAPABILITY_JOURNAL not in dropped
    assert seats.install.event_journal is None
    assert "journal" not in seats.supervisor.names()
    seats.event.emit("resource.changed", resource_ref="y", action="put")
    assert journal.latest_offset() == before


class _LeanShell:
    def __init__(self) -> None:
        self.structure = None
        self.install = None
        self.supervisor = None
        self.workload = None


def test_phase_assemble_seats_journal_on_install_not_supervisor() -> None:
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
    assert board.event_journal is not None
    assert "journal" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_JOURNAL in ctx.structure.materialized_capabilities

    assemble_run(ctx, {"structure_definition_id": LOCAL_EMBEDDED_ID})
    assert board.event_journal is None
    assert CAPABILITY_JOURNAL not in ctx.structure.materialized_capabilities


def test_cli_host_journal_is_one_object_on_the_runtime_bus() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        rt = host.runtime()
        assert host.admission.has_capability(CAPABILITY_JOURNAL)
        assert host.event_journal is not None
        assert host.event_journal is rt.install.event_journal
        assert "journal" not in rt.supervisor.names()

        before = host.event_journal.latest_offset()
        runtime_event_engine(host).emit("job.completed", job_id="j-runtime", status="SUCCEEDED")
        runtime_event_engine(host).emit("resource.changed", resource_ref="x", action="put")
        after_runtime = host.event_journal.latest_offset()
        assert after_runtime >= before + 2

        host.event.emit("resource.changed", resource_ref="y", action="put")
        assert host.event_journal.latest_offset() == after_runtime
    finally:
        host.shutdown()


def test_embedded_host_still_omits_journal() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert not host.admission.has_capability(CAPABILITY_JOURNAL)
        assert host.event_journal is None
        rt = host.runtime()
        assert rt.install.event_journal is None
        assert rt.supervisor is None or "journal" not in rt.supervisor.names()
    finally:
        host.shutdown()


def test_inventory_journal_leftover_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "structure.journal_one_organ" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["structure.journal_composition_king"] == "paid_0_67_7"
    assert pretenders["structure.journal_supervisor_costume"] == "paid_0_67_8"
    assert admission_inventory()["gated_count"] >= 1
