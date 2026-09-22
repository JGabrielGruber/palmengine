"""0.63.5 — structure-definition seed map from mode / composition (not dual law)."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import (
    LOCAL_ALL_IN_ONE_ID,
    LOCAL_CLI_ID,
    LOCAL_EMBEDDED_ID,
    LOCAL_SERVER_ID,
    LOCAL_WORKER_ID,
    resolve_builtin_definition,
)
from palm.system.log import reset_system_log_for_tests
from palm.system.structure.seed import (
    definition_id_for_boot_mode,
    definition_id_for_composition,
    resolve_seed_definition,
)


def test_mode_to_definition_ids() -> None:
    assert definition_id_for_boot_mode("safe") == LOCAL_EMBEDDED_ID
    assert definition_id_for_boot_mode("test") == LOCAL_EMBEDDED_ID
    assert definition_id_for_boot_mode("cli") == LOCAL_CLI_ID
    assert definition_id_for_boot_mode("server") == LOCAL_SERVER_ID
    assert definition_id_for_boot_mode("prod") == LOCAL_SERVER_ID
    assert definition_id_for_boot_mode("worker") == LOCAL_WORKER_ID
    assert definition_id_for_boot_mode("dev") == LOCAL_ALL_IN_ONE_ID
    assert definition_id_for_boot_mode(None) is None


def test_composition_inference() -> None:
    assert (
        definition_id_for_composition(services=("execution",), surfaces=(), capabilities=())
        == LOCAL_WORKER_ID
    )
    assert (
        definition_id_for_composition(
            services=("execution", "definitions"),
            surfaces=(),
            capabilities=frozenset({"journal"}),
        )
        == LOCAL_CLI_ID
    )
    assert (
        definition_id_for_composition(
            services=("execution",),
            surfaces=("rest",),
            capabilities=frozenset(),
        )
        == LOCAL_SERVER_ID
    )
    assert (
        definition_id_for_composition(services=(), surfaces=(), capabilities=())
        == LOCAL_EMBEDDED_ID
    )


def test_resolve_seed_explicit_wins() -> None:
    definition = resolve_seed_definition(
        mode_name="server", explicit_definition_id="local.cli"
    )
    assert definition.id == LOCAL_CLI_ID


def test_builtin_refuse_differs() -> None:
    emb = resolve_builtin_definition(LOCAL_EMBEDDED_ID)
    cli = resolve_builtin_definition(LOCAL_CLI_ID)
    assert "background_drain" not in emb.refuse
    assert "background_drain" not in cli.refuse
    assert "server_surfaces" in cli.refuse
    assert "work_drain" not in emb.capabilities
    assert "work_drain" in cli.capabilities


def test_host_for_mode_cli_seeds_cli_definition() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost.for_mode(BootMode.cli(), settings=settings)
    host.start()
    try:
        rt = host.runtime()
        assert rt.admission.may_run_business is True
        assert rt.admission.definition_id == LOCAL_CLI_ID
        assert rt.structure is not None
        assert rt.structure.definition is not None
        assert "server_surfaces" in rt.structure.definition.refuse
    finally:
        host.shutdown()


def test_host_for_mode_safe_seeds_embedded() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost.for_mode("safe", settings=settings)
    host.start()
    try:
        rt = host.runtime()
        assert rt.admission.definition_id == LOCAL_EMBEDDED_ID
    finally:
        host.shutdown()


def test_host_explicit_definition_override() -> None:
    reset_system_log_for_tests()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost.for_mode("cli", settings=settings)
    host.start(structure_definition_id="local.embedded")
    try:
        rt = host.runtime()
        assert rt.admission.definition_id == LOCAL_EMBEDDED_ID
    finally:
        host.shutdown()
