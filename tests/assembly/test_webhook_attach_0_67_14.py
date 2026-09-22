"""webhook leftover — one dispatcher, URLs on that object, not a loop (0.67.14)."""

from __future__ import annotations

from dataclasses import replace

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.common.events.external import WebhookDispatcher, webhook_targets_from_urls
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.structure import (
    CAPABILITY_WEBHOOK,
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


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def _webhook_seats() -> CapabilitySeats:
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


def test_webhook_is_not_a_supervisor_loop() -> None:
    seats = _webhook_seats()
    apply_local_capabilities(local_cli(), seats)
    assert seats.install.webhook is not None
    assert "webhook" not in seats.supervisor.names()
    assert "webhook" not in {d.name for d in DEFAULT_CONTINUOUS_DEFINITIONS}


def test_drop_on_omit_clears_without_a_service() -> None:
    seats = _webhook_seats()
    apply_local_capabilities(local_cli(), seats)
    bag = seats.install.webhook
    dropped = apply_local_capabilities(local_embedded(), seats)
    assert CAPABILITY_WEBHOOK not in dropped
    assert seats.install.webhook is None
    assert "webhook" not in seats.supervisor.names()
    assert bag is not seats.install.webhook


class _LeanShell:
    def __init__(self) -> None:
        self.structure = None
        self.install = None
        self.supervisor = None
        self.workload = None


def test_phase_assemble_seats_webhook_on_install_not_supervisor() -> None:
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
    assert board.webhook is not None
    assert "webhook" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_WEBHOOK in ctx.structure.materialized_capabilities

    assemble_run(ctx, {"structure_definition_id": LOCAL_EMBEDDED_ID})
    assert board.webhook is None
    assert CAPABILITY_WEBHOOK not in ctx.structure.materialized_capabilities


def test_dispatcher_replace_targets_is_in_place() -> None:
    dispatcher = WebhookDispatcher([])
    targets = webhook_targets_from_urls(["https://example.test/hook"])
    dispatcher.replace_targets(targets)
    assert dispatcher.targets == tuple(targets)
    dispatcher.replace_targets([])
    assert dispatcher.targets == ()


def test_cli_host_webhook_is_the_install_object_even_without_urls() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        rt = host.runtime()
        assert host.admission.has_capability(CAPABILITY_WEBHOOK)
        assert rt.install.webhook is not None
        assert host.webhook_dispatcher is rt.install.webhook
        assert host._recovery.webhook_dispatcher is rt.install.webhook
        assert host.webhook_dispatcher.targets == ()
        assert "webhook" not in rt.supervisor.names()
    finally:
        host.shutdown()


def test_cli_host_webhook_urls_refine_the_same_object() -> None:
    reset_system_log_for_tests()
    settings = replace(_lean(), webhook_urls=["https://example.test/hook"])
    host = ApplicationHost.for_mode(BootMode.cli(), settings=settings)
    host.start()
    try:
        rt = host.runtime()
        organ = rt.install.webhook
        assert organ is not None
        assert host.webhook_dispatcher is organ
        assert host._recovery.webhook_dispatcher is organ
        assert [t.url for t in organ.targets] == ["https://example.test/hook"]
    finally:
        host.shutdown()


def test_embedded_host_still_omits_webhook() -> None:
    reset_system_log_for_tests()
    settings = replace(_lean(), webhook_urls=["https://example.test/hook"])
    host = ApplicationHost.for_mode(BootMode.safe(), settings=settings)
    host.start()
    try:
        assert not host.admission.has_capability(CAPABILITY_WEBHOOK)
        assert host.webhook_dispatcher is None
        assert host._recovery.webhook_dispatcher is None
        rt = host.runtime()
        assert rt.install.webhook is None
        assert rt.supervisor is None or "webhook" not in rt.supervisor.names()
    finally:
        host.shutdown()


def test_inventory_webhook_leftover_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "structure.webhook_one_organ" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["structure.webhook_composition_king"] == "paid_0_67_13"
    assert pretenders["structure.webhook_recover_twin"] == "paid_0_67_14"
    assert admission_inventory()["gated_count"] >= 1
