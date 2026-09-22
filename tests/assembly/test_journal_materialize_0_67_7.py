"""journal materialize — definition capabilities are the install list (0.67.7)."""

from __future__ import annotations

from dataclasses import replace

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.host.composition import composition_profile_from_name
from bundles.standard.app.settings import PalmSettings
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.structure import (
    CAPABILITY_JOURNAL,
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


def test_builtin_dna_lists_journal_on_attach_phenotypes() -> None:
    assert CAPABILITY_JOURNAL not in local_embedded().capabilities
    assert CAPABILITY_JOURNAL not in local_worker().capabilities
    assert local_cli().has_capability(CAPABILITY_JOURNAL)
    assert local_server().has_capability(CAPABILITY_JOURNAL)
    assert local_all_in_one().has_capability(CAPABILITY_JOURNAL)
    assert local_mcp().has_capability(CAPABILITY_JOURNAL)
    roundtrip = local_cli().from_dict(local_cli().to_dict())
    assert CAPABILITY_JOURNAL in roundtrip.capabilities
    unknown = resolve_builtin_definition("local.unknown")
    assert not unknown.has_capability(CAPABILITY_JOURNAL)


def _journal_seats(supervisor: SystemSupervisor) -> CapabilitySeats:
    event = EventEngine()
    event.initialize()
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    board = SystemInstall()
    board.bind(event=event, storage=storage)
    return CapabilitySeats(supervisor=supervisor, event=event, storage=storage, install=board)


def test_walker_table_owns_journal_not_a_private_if() -> None:
    assert "journal" in LOCAL_CAPABILITY_HANDS
    seen: list[bool] = []

    def extra(seats: CapabilitySeats, *, listed: bool) -> None:
        seen.append(listed)

    LOCAL_CAPABILITY_HANDS["test.extra"] = extra
    try:
        apply_local_capabilities(
            local_cli().from_dict(
                {**local_cli().to_dict(), "capabilities": ["journal", "test.extra"]}
            ),
            _journal_seats(SystemSupervisor(definitions=())),
        )
        assert seen == [True]
    finally:
        del LOCAL_CAPABILITY_HANDS["test.extra"]


def test_materialize_attaches_journal_only_when_listed() -> None:
    sup = SystemSupervisor(definitions=())
    seats = _journal_seats(sup)
    applied = apply_local_capabilities(local_cli(), seats)
    assert CAPABILITY_JOURNAL in applied
    assert seats.install.event_journal is not None
    assert "journal" not in sup.names()
    seats.event.emit("resource.changed", resource_ref="x", action="put")
    assert seats.install.event_journal.latest_offset() >= 1

    dropped = apply_local_capabilities(local_embedded(), seats)
    assert CAPABILITY_JOURNAL not in dropped
    assert seats.install.event_journal is None
    assert "journal" not in sup.names()


def test_wire_catalog_does_not_freelance_register_journal() -> None:
    board = SystemInstall()
    event = EventEngine()
    event.initialize()
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    board.bind(event=event, storage=storage)
    sup = SystemSupervisor()
    sup.install(board)
    assert "journal" not in {d.name for d in sup.definitions()}
    assert "journal" not in sup.names()
    seats = _journal_seats(sup)
    apply_local_capabilities(local_cli(), seats)
    assert "journal" not in sup.names()
    assert seats.install.event_journal is not None


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
    assemble_run(ctx, {"structure_definition_id": definition_id})
    return ctx, supervisor, board


def test_phase_assemble_materializes_journal_from_ctx_board() -> None:
    ctx, supervisor, board = _assemble_from_ctx_seats(definition_id=LOCAL_CLI_ID)
    assert board.event_journal is not None
    assert "journal" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_JOURNAL in ctx.structure.materialized_capabilities


def test_phase_assemble_embedded_does_not_register_journal() -> None:
    ctx, supervisor, board = _assemble_from_ctx_seats(definition_id=LOCAL_EMBEDDED_ID)
    assert board.event_journal is None
    assert "journal" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_JOURNAL not in ctx.structure.materialized_capabilities


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def test_embedded_host_does_not_wire_journal() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_EMBEDDED_ID
        assert not host.admission.has_capability(CAPABILITY_JOURNAL)
        rt = host.runtime()
        assert CAPABILITY_JOURNAL not in rt.structure.materialized_capabilities
        assert rt.supervisor is None or "journal" not in rt.supervisor.names()
        assert host.event_journal is None
    finally:
        host.shutdown()


def test_cli_host_wires_journal_even_when_composition_omits_it() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(
        BootMode.cli(),
        settings=_lean(),
        composition=replace(composition_profile_from_name("cli"), capabilities=frozenset()),
    )
    assert not host.composition.has("journal")
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_CLI_ID
        assert host.admission.has_capability(CAPABILITY_JOURNAL)
        rt = host.runtime()
        assert CAPABILITY_JOURNAL in rt.structure.materialized_capabilities
        assert "journal" not in rt.supervisor.names()
        assert host.event_journal is rt.install.event_journal
        assert host.event_journal is not None
    finally:
        host.shutdown()


def test_mcp_dna_lists_and_wires_journal() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("mcp", settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_MCP_ID
        assert host.admission.has_capability(CAPABILITY_JOURNAL)
        rt = host.runtime()
        assert CAPABILITY_JOURNAL in rt.structure.materialized_capabilities
        assert host.event_journal is rt.install.event_journal
        assert host.event_journal is not None
    finally:
        host.shutdown()


def test_inventory_journal_materialize_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "structure.journal_materialize" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["structure.journal_composition_king"] == "paid_0_67_7"
    assert admission_inventory()["gated_count"] >= 1


def test_worker_dna_omits_journal() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("worker", settings=_lean())
    host.start()
    try:
        assert not host.admission.has_capability(CAPABILITY_JOURNAL)
        rt = host.runtime()
        assert CAPABILITY_JOURNAL not in rt.structure.materialized_capabilities
        assert host.event_journal is None
    finally:
        host.shutdown()
