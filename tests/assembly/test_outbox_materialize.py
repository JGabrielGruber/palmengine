"""outbox materialize — definition capabilities are the install list."""

from __future__ import annotations

from dataclasses import replace

from palm.app.host.application_host import ApplicationHost
from palm.app.host.boot.modes import BootMode
from palm.app.host.composition import CompositionProfile as CP
from palm.app.settings import PalmSettings
from palm.core.structure import (
    CAPABILITY_OUTBOX,
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
    register_outbox,
)


def test_builtin_dna_lists_outbox_on_drain_phenotypes() -> None:
    assert CAPABILITY_OUTBOX not in local_embedded().capabilities
    assert CAPABILITY_OUTBOX not in local_mcp().capabilities
    assert local_cli().has_capability(CAPABILITY_OUTBOX)
    assert local_server().has_capability(CAPABILITY_OUTBOX)
    assert local_all_in_one().has_capability(CAPABILITY_OUTBOX)
    assert local_worker().has_capability(CAPABILITY_OUTBOX)
    roundtrip = local_cli().from_dict(local_cli().to_dict())
    assert CAPABILITY_OUTBOX in roundtrip.capabilities
    unknown = resolve_builtin_definition("local.unknown")
    assert not unknown.has_capability(CAPABILITY_OUTBOX)


class _FakePlane:
    def start_background(self) -> None:
        return None

    def stop_background(self) -> None:
        return None

    def status(self) -> dict[str, object]:
        return {"name": "work_drain", "running": False}


class _FakeStore:
    def pending_count(self) -> int:
        return 0


class _FakeProc:
    def process_batch(self, *, limit: int = 50) -> int:
        return 0

    def recover_pending(self, *, replay_handlers: bool = False) -> int:
        return 0


def _outbox_seats(supervisor: SystemSupervisor) -> CapabilitySeats:
    return CapabilitySeats(
        supervisor=supervisor,
        work_plane=_FakePlane(),
        outbox_store=_FakeStore(),
        outbox_processor=_FakeProc(),
    )


def test_walker_table_owns_outbox_not_a_private_if() -> None:
    assert "outbox" in LOCAL_CAPABILITY_HANDS
    seen: list[bool] = []

    def extra(seats: CapabilitySeats, *, listed: bool) -> None:
        seen.append(listed)

    LOCAL_CAPABILITY_HANDS["test.extra"] = extra
    try:
        apply_local_capabilities(
            local_cli().from_dict(
                {**local_cli().to_dict(), "capabilities": ["outbox", "test.extra"]}
            ),
            _outbox_seats(SystemSupervisor(definitions=())),
        )
        assert seen == [True]
    finally:
        del LOCAL_CAPABILITY_HANDS["test.extra"]


def test_materialize_registers_outbox_only_when_listed() -> None:
    sup = SystemSupervisor(definitions=())
    applied = apply_local_capabilities(local_cli(), _outbox_seats(sup))
    assert CAPABILITY_OUTBOX in applied
    assert "outbox" in sup.names()

    dropped = apply_local_capabilities(local_embedded(), _outbox_seats(sup))
    assert CAPABILITY_OUTBOX not in dropped
    assert "outbox" not in sup.names()


def test_wire_catalog_does_not_freelance_register_outbox() -> None:
    """Default install walks no organs. The hand is the only register."""
    board = SystemInstall()
    board.bind(
        work_plane=_FakePlane(),
        outbox_store=_FakeStore(),
        outbox_processor=_FakeProc(),
    )
    sup = SystemSupervisor()
    sup.install(board)
    assert "outbox" not in {d.name for d in sup.definitions()}
    assert "outbox" not in sup.names()
    apply_local_capabilities(local_cli(), _outbox_seats(sup))
    assert "outbox" in sup.names()


def test_materialize_unregisters_outbox_when_unlisted() -> None:
    """Reassemble still drops a registered service when DNA omits the name."""
    sup = SystemSupervisor(definitions=())
    register_outbox(
        sup,
        ContinuousWireContext(outbox_store=_FakeStore(), outbox_processor=_FakeProc()),
    )
    assert "outbox" in sup.names()
    apply_local_capabilities(local_embedded(), _outbox_seats(sup))
    assert "outbox" not in sup.names()


class _LeanShell:
    def __init__(self) -> None:
        self.structure = None
        self.install = None
        self.supervisor = None
        self.workload = None


def _assemble_from_ctx_seats(*, definition_id: str) -> tuple[BootContext, SystemSupervisor]:
    reset_system_log_for_tests()
    board = SystemInstall()
    board.bind(
        work_plane=_FakePlane(),
        outbox_store=_FakeStore(),
        outbox_processor=_FakeProc(),
    )
    supervisor = SystemSupervisor(definitions=())
    ctx = BootContext(
        schedule="system",
        shell=_LeanShell(),
        install=board,
        supervisor=supervisor,
    )
    assemble_run(ctx, {"structure_definition_id": definition_id})
    return ctx, supervisor


def test_phase_assemble_materializes_outbox_from_ctx_board() -> None:
    ctx, supervisor = _assemble_from_ctx_seats(definition_id=LOCAL_CLI_ID)
    assert "outbox" in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_OUTBOX in ctx.structure.materialized_capabilities


def test_phase_assemble_embedded_does_not_register_outbox() -> None:
    ctx, supervisor = _assemble_from_ctx_seats(definition_id=LOCAL_EMBEDDED_ID)
    assert "outbox" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_OUTBOX not in ctx.structure.materialized_capabilities


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def test_embedded_host_does_not_start_outbox() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_EMBEDDED_ID
        rt = host.runtime()
        assert rt.structure is not None
        assert CAPABILITY_OUTBOX not in rt.structure.materialized_capabilities
        assert rt.supervisor is None or "outbox" not in rt.supervisor.names()
        assert rt.outbox_store is None
    finally:
        host.shutdown()


def test_cli_host_starts_outbox_even_when_composition_omits_it() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(
        BootMode.cli(),
        settings=_lean(),
        composition=replace(CP.cli(), capabilities=frozenset()),
    )
    assert not host.composition.has("outbox")
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_CLI_ID
        rt = host.runtime()
        assert rt.structure is not None
        assert CAPABILITY_OUTBOX in rt.structure.materialized_capabilities
        assert "outbox" in rt.supervisor.names()
        assert rt.outbox_store is not None
        assert "outbox" in rt.supervisor.status()["running"]
    finally:
        host.shutdown()


def test_server_dna_starts_outbox() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("server", settings=_lean(), server_port=0)
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_SERVER_ID
        rt = host.runtime()
        assert CAPABILITY_OUTBOX in rt.structure.materialized_capabilities
        assert "outbox" in rt.supervisor.names()
        assert "outbox" in rt.supervisor.status()["running"]
    finally:
        host.shutdown()


def test_mcp_dna_does_not_list_or_start_outbox() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("mcp", settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_MCP_ID
        rt = host.runtime()
        assert CAPABILITY_OUTBOX not in rt.structure.materialized_capabilities
        assert rt.supervisor is None or "outbox" not in rt.supervisor.names()
        assert rt.outbox_store is None
    finally:
        host.shutdown()


def test_packaging_has_no_outbox_service_flag() -> None:
    """DNA lists the name. Settings and deployment do not keep a dead switch."""
    from palm.app.host.roles import DeploymentProfile
    from palm.app.settings import PalmSettings as Settings

    assert "enable_outbox_service" not in Settings.__dataclass_fields__
    assert "enable_outbox_service" not in DeploymentProfile.__dataclass_fields__
    assert "enable_outbox_background" not in Settings.__dataclass_fields__
