"""0.63.13 — env structure seed (SD-021): definition from settings; drain listed on definition."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import (
    CAPABILITY_WORK_DRAIN,
    LOCAL_CLI_ID,
    LOCAL_EMBEDDED_ID,
)
from palm.system.log import reset_system_log_for_tests
from palm.system.structure import (
    STRUCTURE_SEED_ENV,
    definition_id_from_settings,
    resolve_seed_definition,
    seed_structure_options_from_host,
)


def test_structure_seed_env_catalog() -> None:
    envs = {row["env"] for row in STRUCTURE_SEED_ENV}
    assert "PALM_STRUCTURE_DEFINITION_ID" in envs
    assert "PALM_ENABLE_WORK_DRAIN_SERVICE" not in envs


def test_definition_id_from_settings() -> None:
    assert definition_id_from_settings(None) is None
    s = PalmSettings.for_tests(load_examples=False)
    assert definition_id_from_settings(s) is None
    s3 = PalmSettings(
        load_example_definitions=False,
        storage_backend="memory",
        structure_definition_id="local.cli",
        rebuild_projections_on_startup=False,
        reconcile_instances_on_startup=False,
    )
    assert definition_id_from_settings(s3) == LOCAL_CLI_ID


def test_settings_definition_wins_over_mode_in_seed() -> None:
    settings = PalmSettings(
        load_example_definitions=False,
        storage_backend="memory",
        structure_definition_id="local.cli",
        rebuild_projections_on_startup=False,
        reconcile_instances_on_startup=False,
    )
    host = ApplicationHost.for_mode(BootMode.safe(), settings=settings)
    seed = seed_structure_options_from_host(host)
    assert seed["structure_definition_id"] == LOCAL_CLI_ID
    assert seed["structure_definition"].id == LOCAL_CLI_ID


def test_host_settings_definition_id_loads() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings(
        load_example_definitions=False,
        storage_backend="memory",
        structure_definition_id="local.cli",
        rebuild_projections_on_startup=False,
        reconcile_instances_on_startup=False,
    )
    # safe mode composition is embedded (no surfaces); definition from settings → cli
    host = ApplicationHost.for_mode("safe", settings=settings)
    host.start()
    try:
        assert host.admission.definition_id == LOCAL_CLI_ID
        assert host.admission.may_run_business is True
    finally:
        host.shutdown()


def test_definition_override_does_not_use_composition_as_drain_membership() -> None:
    """CLI composition still lists work_drain. Embedded definition does not. Omit is enough."""
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost.for_mode("cli", settings=settings)
    assert not host.composition.has("work_drain")
    host.start(structure_definition_id="local.embedded")
    try:
        assert host.admission.definition_id == LOCAL_EMBEDDED_ID
        assert host.admission.may_run_business is True
        reasons = host.admission.reasons
        assert not any("refuse:background_drain" in str(r) for r in reasons)
        rt = host.runtime()
        assert CAPABILITY_WORK_DRAIN not in rt.structure.materialized_capabilities
        assert rt.supervisor is None or "work_drain" not in rt.supervisor.names()
    finally:
        host.shutdown()


def test_resolve_seed_explicit_from_settings_path() -> None:
    definition = resolve_seed_definition(
        mode_name="server", explicit_definition_id="local.embedded"
    )
    assert definition.id == LOCAL_EMBEDDED_ID
