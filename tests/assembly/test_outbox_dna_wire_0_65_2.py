"""0.65.2 — host outbox store wire follows DNA listing (not composition)."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import LOCAL_CLI_ID, LOCAL_EMBEDDED_ID
from palm.system.log import reset_system_log_for_tests
from palm.system.structure.inventory import READINESS_EDGES, admission_inventory


def _lean(**overrides: object) -> PalmSettings:
    base: dict[str, object] = {
        "load_example_definitions": False,
        "storage_backend": "memory",
        "rebuild_projections_on_startup": False,
        "reconcile_instances_on_startup": False,
        "analytics_enabled": False,
    }
    base.update(overrides)
    return PalmSettings(**base)  # type: ignore[arg-type]


def test_host_outbox_wire_follows_dna_omit() -> None:
    """Embedded DNA omits outbox → no store."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_EMBEDDED_ID
        rt = host.runtime()
        assert rt.outbox_store is None
        assert rt.outbox_processor is None
        assert rt.supervisor is None or "outbox" not in rt.supervisor.names()
    finally:
        host.shutdown()


def test_host_outbox_wire_when_dna_lists_outbox() -> None:
    """CLI DNA lists outbox → store wires."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(
        BootMode.cli(),
        settings=_lean(),
    )
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_CLI_ID
        rt = host.runtime()
        assert rt.outbox_store is not None
        assert rt.outbox_processor is not None
        assert "outbox" in rt.supervisor.names()
    finally:
        host.shutdown()


def test_start_option_does_not_override_dna() -> None:
    """0.68.4: CLI DNA still wires; there is no enable_event_outbox override."""
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        rt = host.runtime()
        assert rt.outbox_store is not None
        assert "outbox" in rt.supervisor.names()
    finally:
        host.shutdown()


def test_inventory_outbox_host_paid() -> None:
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["outbox.start_option_seed"] == "paid_0_68_4"
    assert pretenders["runtime.enable_event_outbox_bare"] == "paid_0_68_4"
    assert admission_inventory()["readiness_edge_count"] >= 2
