"""work_drain materialize — definition capabilities are the install list."""

from __future__ import annotations

from dataclasses import replace

from palm.app.host.application_host import ApplicationHost
from palm.app.host.boot.modes import BootMode
from palm.app.host.composition import CompositionProfile as CP
from palm.app.settings import PalmSettings
from palm.core.structure import (
    CAPABILITY_WORK_DRAIN,
    LOCAL_CLI_ID,
    LOCAL_EMBEDDED_ID,
    LOCAL_MCP_ID,
    LOCAL_SERVER_ID,
    local_all_in_one,
    local_cli,
    local_embedded,
    local_mcp,
    local_server,
    local_worker,
    resolve_builtin_definition,
)
from palm.system.boot.context import BootContext
from palm.system.interfaces.install import SystemInstall
from palm.system.log import reset_system_log_for_tests
from palm.system.structure import (
    LOCAL_CAPABILITY_HANDS,
    CapabilitySeats,
    apply_local_capabilities,
)
from palm.system.structure.phase_assemble import run as assemble_run
from palm.system.subsystems.supervisor import SystemSupervisor
from palm.system.subsystems.supervisor.definition import (
    ContinuousWireContext,
    register_work_drain,
)


def test_builtin_dna_lists_work_drain_on_drain_phenotypes() -> None:
    assert CAPABILITY_WORK_DRAIN not in local_embedded().capabilities
    assert CAPABILITY_WORK_DRAIN not in local_mcp().capabilities
    assert local_cli().has_capability(CAPABILITY_WORK_DRAIN)
    assert local_server().has_capability(CAPABILITY_WORK_DRAIN)
    assert local_all_in_one().has_capability(CAPABILITY_WORK_DRAIN)
    assert local_worker().has_capability(CAPABILITY_WORK_DRAIN)
    roundtrip = local_cli().from_dict(local_cli().to_dict())
    assert CAPABILITY_WORK_DRAIN in roundtrip.capabilities
    unknown = resolve_builtin_definition("local.unknown")
    assert not unknown.has_capability(CAPABILITY_WORK_DRAIN)


class _FakePlane:
    def start_background(self) -> None:
        return None

    def stop_background(self) -> None:
        return None

    def status(self) -> dict[str, object]:
        return {"name": "work_drain", "running": False}


def test_walker_table_owns_work_drain_not_a_private_if() -> None:
    assert "work_drain" in LOCAL_CAPABILITY_HANDS
    seen: list[bool] = []

    def extra(seats: CapabilitySeats, *, listed: bool) -> None:
        seen.append(listed)

    LOCAL_CAPABILITY_HANDS["test.extra"] = extra
    try:
        apply_local_capabilities(
            local_cli().from_dict(
                {**local_cli().to_dict(), "capabilities": ["work_drain", "test.extra"]}
            ),
            CapabilitySeats(
                supervisor=SystemSupervisor(definitions=()),
                work_plane=_FakePlane(),
            ),
        )
        assert seen == [True]
    finally:
        del LOCAL_CAPABILITY_HANDS["test.extra"]


def test_materialize_registers_work_drain_only_when_listed() -> None:
    sup = SystemSupervisor(definitions=())
    applied = apply_local_capabilities(
        local_cli(),
        CapabilitySeats(supervisor=sup, work_plane=_FakePlane()),
    )
    assert CAPABILITY_WORK_DRAIN in applied
    assert "work_drain" in sup.names()

    dropped = apply_local_capabilities(
        local_embedded(),
        CapabilitySeats(supervisor=sup, work_plane=_FakePlane()),
    )
    assert dropped == frozenset()
    assert "work_drain" not in sup.names()


def test_wire_catalog_does_not_freelance_register_work_drain() -> None:
    """Default install walks outbox, not work_drain. The hand is the only register."""
    plane = _FakePlane()
    board = SystemInstall()
    board.bind(work_plane=plane)
    sup = SystemSupervisor()
    sup.install(board)
    assert "work_drain" not in {d.name for d in sup.definitions()}
    assert "work_drain" not in sup.names()
    apply_local_capabilities(
        local_cli(),
        CapabilitySeats(supervisor=sup, work_plane=plane),
    )
    assert "work_drain" in sup.names()


def test_materialize_unregisters_work_drain_when_unlisted() -> None:
    """Reassemble still drops a registered service when DNA omits the name."""
    sup = SystemSupervisor(definitions=())
    plane = _FakePlane()
    register_work_drain(sup, ContinuousWireContext(work_plane=plane))
    assert "work_drain" in sup.names()
    apply_local_capabilities(
        local_embedded(),
        CapabilitySeats(supervisor=sup, work_plane=plane),
    )
    assert "work_drain" not in sup.names()


class _LeanShell:
    """No work_plane. Assemble fill must take seats from ctx + board."""

    def __init__(self) -> None:
        self.structure = None
        self.install = None
        self.supervisor = None
        self.workload = None


def _assemble_from_ctx_seats(*, definition_id: str) -> tuple[BootContext, SystemSupervisor]:
    reset_system_log_for_tests()
    board = SystemInstall()
    board.bind(work_plane=_FakePlane())
    supervisor = SystemSupervisor(definitions=())
    ctx = BootContext(
        schedule="system",
        shell=_LeanShell(),
        install=board,
        supervisor=supervisor,
    )
    assemble_run(ctx, {"structure_definition_id": definition_id})
    return ctx, supervisor


def test_phase_assemble_materializes_work_drain_from_ctx_board() -> None:
    ctx, supervisor = _assemble_from_ctx_seats(definition_id=LOCAL_CLI_ID)
    assert not hasattr(ctx.shell, "work_plane")
    assert "work_drain" in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_WORK_DRAIN in ctx.structure.materialized_capabilities


def test_phase_assemble_embedded_does_not_register_work_drain() -> None:
    ctx, supervisor = _assemble_from_ctx_seats(definition_id=LOCAL_EMBEDDED_ID)
    assert "work_drain" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_WORK_DRAIN not in ctx.structure.materialized_capabilities


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def test_embedded_host_does_not_start_drain() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_EMBEDDED_ID
        plane = host.runtime().work_plane
        assert plane is None or plane.is_running is False
        rt = host.runtime()
        assert rt.structure is not None
        assert CAPABILITY_WORK_DRAIN not in rt.structure.materialized_capabilities
        assert rt.supervisor is None or "work_drain" not in rt.supervisor.names()
    finally:
        host.shutdown()


def test_cli_host_starts_drain_even_when_composition_omits_it() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(
        BootMode.cli(),
        settings=_lean(),
        composition=replace(CP.cli(), capabilities=frozenset()),
    )
    assert not host.composition.has("work_drain")
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_CLI_ID
        assert host.admission.may_run_business is True
        rt = host.runtime()
        assert rt.work_plane is not None
        assert rt.work_plane.is_running is True
        assert rt.structure is not None
        assert CAPABILITY_WORK_DRAIN in rt.structure.materialized_capabilities
        assert "work_drain" in rt.supervisor.names()
    finally:
        host.shutdown()


def test_server_dna_starts_drain() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("server", settings=_lean(), server_port=0)
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_SERVER_ID
        rt = host.runtime()
        assert CAPABILITY_WORK_DRAIN in rt.structure.materialized_capabilities
        assert "work_drain" in rt.supervisor.names()
        assert rt.work_plane is not None
        assert rt.work_plane.is_running is True
    finally:
        host.shutdown()


def test_boot_mode_cannot_forbid_drain_when_dna_lists_it() -> None:
    """Test mode is not a peer OR. CLI DNA still lists and starts drain."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.test(), settings=_lean())
    host.start(structure_definition_id=LOCAL_CLI_ID)
    try:
        assert host.boot_mode is not None
        assert host.admission.definition_id == LOCAL_CLI_ID
        rt = host.runtime()
        assert CAPABILITY_WORK_DRAIN in rt.structure.materialized_capabilities
        assert "work_drain" in rt.supervisor.names()
        assert host.runtime().work_plane is not None
        assert host.runtime().work_plane.is_running is True
    finally:
        host.shutdown()


def test_mcp_dna_does_not_list_or_start_drain() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("mcp", settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_MCP_ID
        rt = host.runtime()
        assert CAPABILITY_WORK_DRAIN not in rt.structure.materialized_capabilities
        assert rt.supervisor is None or "work_drain" not in rt.supervisor.names()
        plane = rt.work_plane
        assert plane is None or plane.is_running is False
    finally:
        host.shutdown()


def test_assemble_uses_shell_assembly_seat() -> None:
    """Assemble reads and writes the seat. No getattr bag scrape."""
    import inspect

    from palm.system.structure.phase_assemble import run as _run

    src = inspect.getsource(_run)
    assert 'getattr(shell, "structure"' not in src
    ctx, _ = _assemble_from_ctx_seats(definition_id=LOCAL_CLI_ID)
    assert ctx.shell.structure is ctx.structure
    assert ctx.structure is not None


def test_packaging_has_no_work_drain_service_flag() -> None:
    """DNA lists the name. Settings and deployment do not keep a dead switch."""
    from palm.app.host.roles import DeploymentProfile
    from palm.app.settings import PalmSettings

    assert "enable_work_drain_service" not in PalmSettings.__dataclass_fields__
    assert "enable_work_drain_service" not in DeploymentProfile.__dataclass_fields__


def test_host_does_not_alias_start_plane() -> None:
    """Plane lives on the runtime. Host start_plane is costume."""
    assert not hasattr(ApplicationHost, "start_plane")


def test_coordinator_has_no_start_plane_alias() -> None:
    from palm.app.host.workplane.coordinator import WorkPlaneCoordinator

    assert not hasattr(WorkPlaneCoordinator, "_start_plane")
    assert not hasattr(WorkPlaneCoordinator, "start_background")
    assert not hasattr(WorkPlaneCoordinator, "stop_background")


def test_coordinator_tick_reads_runtime_work_plane() -> None:
    from palm.app.host.workplane.coordinator import WorkPlaneCoordinator

    class _Plane:
        def tick(self, *, limit: int = 10) -> int:
            return limit

        def tick_schedules(self) -> int:
            return 2

    class _Runtime:
        work_plane = _Plane()

    class _Host:
        def runtime(self):
            return _Runtime()

    n = WorkPlaneCoordinator(_Host()).tick_work(limit=3)  # type: ignore[arg-type]
    assert n == 5
