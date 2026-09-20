"""projections materialize — definition capabilities are the install list (0.67.9)."""

from __future__ import annotations

from dataclasses import replace

from palm.app.host.application_host import ApplicationHost
from palm.app.host.boot.modes import BootMode
from palm.app.host.composition import CompositionProfile as CP
from palm.app.settings import PalmSettings
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.structure import (
    CAPABILITY_PROJECTIONS,
    LOCAL_CLI_ID,
    LOCAL_EMBEDDED_ID,
    LOCAL_MCP_ID,
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
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES, admission_inventory
from palm.system.structure.phase_assemble import run as assemble_run
from palm.system.subsystems.supervisor import SystemSupervisor


def test_builtin_dna_lists_projections_on_attach_phenotypes() -> None:
    assert CAPABILITY_PROJECTIONS not in local_embedded().capabilities
    assert CAPABILITY_PROJECTIONS not in local_worker().capabilities
    assert local_cli().has_capability(CAPABILITY_PROJECTIONS)
    assert local_server().has_capability(CAPABILITY_PROJECTIONS)
    assert local_all_in_one().has_capability(CAPABILITY_PROJECTIONS)
    assert local_mcp().has_capability(CAPABILITY_PROJECTIONS)
    roundtrip = local_cli().from_dict(local_cli().to_dict())
    assert CAPABILITY_PROJECTIONS in roundtrip.capabilities
    unknown = resolve_builtin_definition("local.unknown")
    assert not unknown.has_capability(CAPABILITY_PROJECTIONS)


def _projections_seats(supervisor: SystemSupervisor) -> CapabilitySeats:
    event = EventEngine()
    event.initialize()
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    board = SystemInstall()
    board.bind(event=event, storage=storage, instance_manager=object())
    return CapabilitySeats(supervisor=supervisor, event=event, storage=storage, install=board)


def test_walker_table_owns_projections_not_a_private_if() -> None:
    assert "projections" in LOCAL_CAPABILITY_HANDS
    seen: list[bool] = []

    def extra(seats: CapabilitySeats, *, listed: bool) -> None:
        seen.append(listed)

    LOCAL_CAPABILITY_HANDS["test.extra"] = extra
    try:
        apply_local_capabilities(
            local_cli().from_dict(
                {**local_cli().to_dict(), "capabilities": ["projections", "test.extra"]}
            ),
            _projections_seats(SystemSupervisor(definitions=())),
        )
        assert seen == [True]
    finally:
        del LOCAL_CAPABILITY_HANDS["test.extra"]


def test_materialize_attaches_projections_only_when_listed() -> None:
    sup = SystemSupervisor(definitions=())
    seats = _projections_seats(sup)
    applied = apply_local_capabilities(local_cli(), seats)
    assert CAPABILITY_PROJECTIONS in applied
    assert seats.install.projections is not None
    assert "projections" not in sup.names()

    dropped = apply_local_capabilities(local_embedded(), seats)
    assert CAPABILITY_PROJECTIONS not in dropped
    assert seats.install.projections is None
    assert "projections" not in sup.names()


def test_wire_catalog_does_not_freelance_register_projections() -> None:
    board = SystemInstall()
    event = EventEngine()
    event.initialize()
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    board.bind(event=event, storage=storage, instance_manager=object())
    sup = SystemSupervisor()
    sup.install(board)
    assert "projections" not in {d.name for d in sup.definitions()}
    assert "projections" not in sup.names()
    seats = _projections_seats(sup)
    apply_local_capabilities(local_cli(), seats)
    assert "projections" not in sup.names()
    assert seats.install.projections is not None


class _LeanShell:
    def __init__(self) -> None:
        self.structure = None
        self.install = None
        self.supervisor = None
        self.workload = None


def _assemble_from_ctx_seats(
    *, definition_id: str
) -> tuple[BootContext, SystemSupervisor, SystemInstall]:
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
    assemble_run(ctx, {"structure_definition_id": definition_id})
    return ctx, supervisor, board


def test_phase_assemble_materializes_projections_from_ctx_board() -> None:
    ctx, supervisor, board = _assemble_from_ctx_seats(definition_id=LOCAL_CLI_ID)
    assert board.projections is not None
    assert "projections" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_PROJECTIONS in ctx.structure.materialized_capabilities


def test_phase_assemble_embedded_does_not_register_projections() -> None:
    ctx, supervisor, board = _assemble_from_ctx_seats(definition_id=LOCAL_EMBEDDED_ID)
    assert board.projections is None
    assert "projections" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_PROJECTIONS not in ctx.structure.materialized_capabilities


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def test_embedded_host_does_not_wire_projections() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_EMBEDDED_ID
        assert not host.admission.has_capability(CAPABILITY_PROJECTIONS)
        rt = host.runtime()
        assert CAPABILITY_PROJECTIONS not in rt.structure.materialized_capabilities
        assert rt.supervisor is None or "projections" not in rt.supervisor.names()
        assert host._instance_projection is None
        assert rt.install.projections is None
    finally:
        host.shutdown()


def test_cli_host_wires_projections_even_when_composition_omits_it() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(
        BootMode.cli(),
        settings=_lean(),
        composition=replace(CP.cli(), capabilities=frozenset()),
    )
    assert not host.composition.has("projections")
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_CLI_ID
        assert host.admission.has_capability(CAPABILITY_PROJECTIONS)
        rt = host.runtime()
        assert CAPABILITY_PROJECTIONS in rt.structure.materialized_capabilities
        assert "projections" not in rt.supervisor.names()
        assert rt.install.projections is not None
        assert host._instance_projection is not None
    finally:
        host.shutdown()


def test_mcp_dna_lists_and_wires_projections() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("mcp", settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_MCP_ID
        assert host.admission.has_capability(CAPABILITY_PROJECTIONS)
        rt = host.runtime()
        assert CAPABILITY_PROJECTIONS in rt.structure.materialized_capabilities
        assert host._instance_projection is not None
        assert rt.install.projections is not None
    finally:
        host.shutdown()


def test_worker_dna_omits_projections() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("worker", settings=_lean())
    host.start()
    try:
        assert not host.admission.has_capability(CAPABILITY_PROJECTIONS)
        rt = host.runtime()
        assert CAPABILITY_PROJECTIONS not in rt.structure.materialized_capabilities
        assert host._instance_projection is None
    finally:
        host.shutdown()


def test_inventory_projections_materialize_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "structure.projections_materialize" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["structure.projections_composition_king"] == "paid_0_67_9"
    assert admission_inventory()["gated_count"] >= 1
