"""projections leftover — one attach, one host object, not a loop (0.67.10)."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.common.cqrs.query import GetJobStatusQuery
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.structure import (
    CAPABILITY_PROJECTIONS,
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


def _projections_seats() -> CapabilitySeats:
    event = EventEngine()
    event.initialize()
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    board = SystemInstall()
    board.bind(event=event, storage=storage, instance_manager=object())
    return CapabilitySeats(
        install=board, event=event, storage=storage, supervisor=SystemSupervisor(definitions=())
    )


def test_projections_is_not_a_supervisor_loop() -> None:
    seats = _projections_seats()
    apply_local_capabilities(local_cli(), seats)
    assert seats.install.projections is not None
    assert "projections" not in seats.supervisor.names()
    assert "projections" not in {d.name for d in DEFAULT_CONTINUOUS_DEFINITIONS}


def test_drop_on_omit_unsubscribes_without_a_service() -> None:
    seats = _projections_seats()
    apply_local_capabilities(local_cli(), seats)
    bag = seats.install.projections
    board = bag.job_board
    seats.event.emit("job.completed", job_id="j-before", status="SUCCEEDED")
    before = board.entry_count()
    assert before >= 1
    assert board.get_job(GetJobStatusQuery(job_id="j-before")) is not None

    dropped = apply_local_capabilities(local_embedded(), seats)
    assert CAPABILITY_PROJECTIONS not in dropped
    assert seats.install.projections is None
    assert "projections" not in seats.supervisor.names()
    seats.event.emit("job.completed", job_id="j-after", status="SUCCEEDED")
    assert board.entry_count() == before
    assert board.get_job(GetJobStatusQuery(job_id="j-after")) is None


class _LeanShell:
    def __init__(self) -> None:
        self.structure = None
        self.install = None
        self.supervisor = None
        self.workload = None


def test_phase_assemble_seats_projections_on_install_not_supervisor() -> None:
    reset_system_log_for_tests()
    event = EventEngine()
    event.initialize()
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    board = SystemInstall()
    board.bind(event=event, storage=storage, instance_manager=object())
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
    assert board.projections is not None
    assert "projections" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_PROJECTIONS in ctx.structure.materialized_capabilities

    assemble_run(ctx, {"structure_definition_id": LOCAL_EMBEDDED_ID})
    assert board.projections is None
    assert CAPABILITY_PROJECTIONS not in ctx.structure.materialized_capabilities


def test_cli_host_projections_is_one_object_on_the_runtime_bus() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        rt = host.runtime()
        assert host.admission.has_capability(CAPABILITY_PROJECTIONS)
        assert host._instance_projection is not None
        assert rt.install.projections is not None
        assert host._instance_projection is rt.install.projections.instance
        assert host._job_board_projection is rt.install.projections.job_board
        assert host._resource_projection is rt.install.projections.resource
        assert "projections" not in rt.supervisor.names()

        board = host._job_board_projection
        before = board.entry_count()
        runtime_event_engine(host).emit("job.completed", job_id="j-runtime", status="SUCCEEDED")
        after_runtime = board.entry_count()
        assert after_runtime >= before + 1
        assert board.get_job(GetJobStatusQuery(job_id="j-runtime")) is not None

        host.event.emit("job.completed", job_id="j-host", status="SUCCEEDED")
        assert board.entry_count() == after_runtime
        assert board.get_job(GetJobStatusQuery(job_id="j-host")) is None
    finally:
        host.shutdown()


def test_embedded_host_still_omits_projections() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert not host.admission.has_capability(CAPABILITY_PROJECTIONS)
        assert host._instance_projection is None
        assert host._job_board_projection is None
        rt = host.runtime()
        assert rt.install.projections is None
        assert rt.supervisor is None or "projections" not in rt.supervisor.names()
    finally:
        host.shutdown()


def test_inventory_projections_leftover_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "structure.projections_one_organ" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["structure.projections_composition_king"] == "paid_0_67_9"
    assert pretenders["structure.projections_supervisor_costume"] == "paid_0_67_10"
    assert admission_inventory()["gated_count"] >= 1
