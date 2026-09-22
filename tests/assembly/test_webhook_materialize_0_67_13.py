"""webhook materialize — definition capabilities are the install list (0.67.13)."""

from __future__ import annotations

from dataclasses import replace

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.host.composition import composition_profile_from_name
from bundles.standard.app.settings import PalmSettings
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.structure import (
    CAPABILITY_WEBHOOK,
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


def test_builtin_dna_lists_webhook_on_attach_phenotypes() -> None:
    assert CAPABILITY_WEBHOOK not in local_embedded().capabilities
    assert CAPABILITY_WEBHOOK not in local_worker().capabilities
    assert local_cli().has_capability(CAPABILITY_WEBHOOK)
    assert local_server().has_capability(CAPABILITY_WEBHOOK)
    assert local_all_in_one().has_capability(CAPABILITY_WEBHOOK)
    assert local_mcp().has_capability(CAPABILITY_WEBHOOK)
    roundtrip = local_cli().from_dict(local_cli().to_dict())
    assert CAPABILITY_WEBHOOK in roundtrip.capabilities
    unknown = resolve_builtin_definition("local.unknown")
    assert not unknown.has_capability(CAPABILITY_WEBHOOK)


def _webhook_seats(supervisor: SystemSupervisor) -> CapabilitySeats:
    event = EventEngine()
    event.initialize()
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    board = SystemInstall()
    board.bind(event=event, storage=storage)
    return CapabilitySeats(supervisor=supervisor, event=event, storage=storage, install=board)


def test_walker_table_owns_webhook_not_a_private_if() -> None:
    assert "webhook" in LOCAL_CAPABILITY_HANDS
    seen: list[bool] = []

    def extra(seats: CapabilitySeats, *, listed: bool) -> None:
        seen.append(listed)

    LOCAL_CAPABILITY_HANDS["test.extra"] = extra
    try:
        apply_local_capabilities(
            local_cli().from_dict(
                {**local_cli().to_dict(), "capabilities": ["webhook", "test.extra"]}
            ),
            _webhook_seats(SystemSupervisor(definitions=())),
        )
        assert seen == [True]
    finally:
        del LOCAL_CAPABILITY_HANDS["test.extra"]


def test_materialize_attaches_webhook_only_when_listed() -> None:
    sup = SystemSupervisor(definitions=())
    seats = _webhook_seats(sup)
    applied = apply_local_capabilities(local_cli(), seats)
    assert CAPABILITY_WEBHOOK in applied
    assert seats.install.webhook is not None
    assert "webhook" not in sup.names()

    dropped = apply_local_capabilities(local_embedded(), seats)
    assert CAPABILITY_WEBHOOK not in dropped
    assert seats.install.webhook is None
    assert "webhook" not in sup.names()


def test_wire_catalog_does_not_freelance_register_webhook() -> None:
    board = SystemInstall()
    event = EventEngine()
    event.initialize()
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    board.bind(event=event, storage=storage)
    sup = SystemSupervisor()
    sup.install(board)
    assert "webhook" not in {d.name for d in sup.definitions()}
    assert "webhook" not in sup.names()
    seats = _webhook_seats(sup)
    apply_local_capabilities(local_cli(), seats)
    assert "webhook" not in sup.names()
    assert seats.install.webhook is not None


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


def test_phase_assemble_materializes_webhook_from_ctx_board() -> None:
    ctx, supervisor, board = _assemble_from_ctx_seats(definition_id=LOCAL_CLI_ID)
    assert board.webhook is not None
    assert "webhook" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_WEBHOOK in ctx.structure.materialized_capabilities


def test_phase_assemble_embedded_does_not_register_webhook() -> None:
    ctx, supervisor, board = _assemble_from_ctx_seats(definition_id=LOCAL_EMBEDDED_ID)
    assert board.webhook is None
    assert "webhook" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_WEBHOOK not in ctx.structure.materialized_capabilities


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def test_embedded_host_does_not_wire_webhook() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_EMBEDDED_ID
        assert not host.admission.has_capability(CAPABILITY_WEBHOOK)
        rt = host.runtime()
        assert CAPABILITY_WEBHOOK not in rt.structure.materialized_capabilities
        assert rt.supervisor is None or "webhook" not in rt.supervisor.names()
        assert host._recovery.webhook_dispatcher is None
        assert rt.install.webhook is None
    finally:
        host.shutdown()


def test_cli_host_wires_webhook_even_when_composition_omits_it() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(
        BootMode.cli(),
        settings=_lean(),
        composition=replace(composition_profile_from_name("cli"), capabilities=frozenset()),
    )
    assert not host.composition.has("webhook")
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_CLI_ID
        assert host.admission.has_capability(CAPABILITY_WEBHOOK)
        rt = host.runtime()
        assert CAPABILITY_WEBHOOK in rt.structure.materialized_capabilities
        assert "webhook" not in rt.supervisor.names()
        assert rt.install.webhook is not None
    finally:
        host.shutdown()


def test_mcp_dna_lists_and_wires_webhook() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("mcp", settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_MCP_ID
        assert host.admission.has_capability(CAPABILITY_WEBHOOK)
        rt = host.runtime()
        assert CAPABILITY_WEBHOOK in rt.structure.materialized_capabilities
        assert rt.install.webhook is not None
    finally:
        host.shutdown()


def test_worker_dna_omits_webhook() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("worker", settings=_lean())
    host.start()
    try:
        assert not host.admission.has_capability(CAPABILITY_WEBHOOK)
        rt = host.runtime()
        assert CAPABILITY_WEBHOOK not in rt.structure.materialized_capabilities
        assert rt.install.webhook is None
    finally:
        host.shutdown()


def test_inventory_webhook_materialize_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "structure.webhook_materialize" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["structure.webhook_composition_king"] == "paid_0_67_13"
    assert admission_inventory()["gated_count"] >= 1
