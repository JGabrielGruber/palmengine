"""analytics leftover — one organ, host slot aliases it, enabled refines, not a loop (0.67.17)."""

from __future__ import annotations

from dataclasses import replace

from palm.app.host.application_host import ApplicationHost
from palm.app.host.boot.modes import BootMode
from palm.app.host.composition import composition_profile_from_name
from palm.app.settings import PalmSettings
from palm.common.analytics import AnalyticsOrgan
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.structure import (
    CAPABILITY_ANALYTICS,
    LOCAL_CLI_ID,
    LOCAL_EMBEDDED_ID,
    local_cli,
    local_embedded,
)
from palm.services.analytics import AnalyticsService
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


def _analytics_seats() -> CapabilitySeats:
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


def test_analytics_is_not_a_supervisor_loop() -> None:
    seats = _analytics_seats()
    apply_local_capabilities(local_cli(), seats)
    assert seats.install.analytics is not None
    assert "analytics" not in seats.supervisor.names()
    assert "analytics" not in {d.name for d in DEFAULT_CONTINUOUS_DEFINITIONS}


def test_drop_on_omit_clears_without_a_service() -> None:
    seats = _analytics_seats()
    apply_local_capabilities(local_cli(), seats)
    bag = seats.install.analytics
    dropped = apply_local_capabilities(local_embedded(), seats)
    assert CAPABILITY_ANALYTICS not in dropped
    assert seats.install.analytics is None
    assert "analytics" not in seats.supervisor.names()
    assert bag is not seats.install.analytics


class _LeanShell:
    def __init__(self) -> None:
        self.structure = None
        self.install = None
        self.supervisor = None
        self.workload = None


def test_phase_assemble_seats_analytics_on_install_not_supervisor() -> None:
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
    assert board.analytics is not None
    assert "analytics" not in supervisor.names()
    assert ctx.structure is not None
    assert CAPABILITY_ANALYTICS in ctx.structure.materialized_capabilities

    assemble_run(ctx, {"structure_definition_id": LOCAL_EMBEDDED_ID})
    assert board.analytics is None
    assert CAPABILITY_ANALYTICS not in ctx.structure.materialized_capabilities


def test_organ_replace_enabled_is_in_place() -> None:
    organ = AnalyticsOrgan()
    organ.replace_enabled(False)
    assert organ.enabled is False
    organ.replace_enabled(True)
    assert organ.enabled is True


def test_service_replace_enabled_is_in_place() -> None:
    service = AnalyticsService(definitions=object(), providers=object(), enabled=True)
    service.replace_enabled(False)
    assert service.enabled is False
    service.replace_enabled(True)
    assert service.enabled is True


def test_cli_host_analytics_is_the_install_object() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        rt = host.runtime()
        assert host.admission.has_capability(CAPABILITY_ANALYTICS)
        organ = rt.install.analytics
        assert organ is not None
        assert host.analytics is organ
        assert isinstance(host.analytics, AnalyticsService)
        assert host.analytics.enabled is True
        if host.assist is not None:
            assert host.assist.analytics is organ
        assert "analytics" not in rt.supervisor.names()
    finally:
        host.shutdown()


def test_cli_host_analytics_enabled_refines_the_same_object() -> None:
    reset_system_log_for_tests()
    settings = replace(_lean(), analytics_enabled=False)
    host = ApplicationHost.for_mode(BootMode.cli(), settings=settings)
    host.start()
    try:
        rt = host.runtime()
        organ = rt.install.analytics
        assert organ is not None
        assert host.analytics is organ
        assert host.analytics.enabled is False
    finally:
        host.shutdown()


def test_embedded_host_still_omits_analytics_even_with_product_services() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(
        BootMode.safe(),
        settings=_lean(),
        composition=replace(
            composition_profile_from_name("embedded"),
            services=composition_profile_from_name("all_in_one").services,
        ),
    )
    host.start()
    try:
        assert not host.admission.has_capability(CAPABILITY_ANALYTICS)
        assert host.analytics is None
        if host.assist is not None:
            assert host.assist.analytics is None
        rt = host.runtime()
        assert rt.install.analytics is None
        assert rt.supervisor is None or "analytics" not in rt.supervisor.names()
    finally:
        host.shutdown()


def test_inventory_analytics_leftover_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "structure.analytics_one_organ" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["structure.analytics_composition_king"] == "paid_0_67_16"
    assert pretenders["structure.analytics_product_twin"] == "paid_0_67_17"
    assert admission_inventory()["gated_count"] >= 1
