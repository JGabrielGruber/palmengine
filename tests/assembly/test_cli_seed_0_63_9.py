"""0.63.9 — CLI entry seeds local.cli DNA (dogfood wall)."""

from __future__ import annotations

from bundles.standard.app.session import create_cli_host
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import LOCAL_CLI_ID
from palm.system.log import reset_system_log_for_tests


def test_create_cli_host_seeds_local_cli_dna() -> None:
    reset_system_log_for_tests()
    host = create_cli_host(settings=PalmSettings.for_tests(load_examples=False))
    try:
        assert host.boot_mode is not None
        assert host.boot_mode.name == "cli"
        assert host.admission.definition_id == LOCAL_CLI_ID
        assert host.admission.may_run_business is True
        rt = host.runtime()
        assert rt.structure is not None
        assert rt.structure.definition is not None
        assert "server_surfaces" in rt.structure.definition.refuse
        assert "background_drain" not in rt.structure.definition.refuse
    finally:
        host.shutdown()
