"""0.63.21 — assist product start is a business path that needs admission; menu nests admission."""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.settings import PalmSettings
from palm.services.assist.catalog.menu import build_menu_page, menu_for_assist
from palm.system.log import reset_system_log_for_tests
from palm.system.structure.errors import AdmissionRefusedError


def _settings() -> PalmSettings:
    # Examples on so operator-entry scenario is registered; lean recovery flags.
    return PalmSettings(
        load_example_definitions=True,
        storage_backend="memory",
        rebuild_projections_on_startup=False,
        reconcile_instances_on_startup=False,
    )


def test_assist_start_scenario_refused_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    # all_in_one composition includes assist service
    host = ApplicationHost.for_mode("all_in_one", settings=_settings())
    host.start(structure_skip=True)
    try:
        assert host.assist is not None
        assert host.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            host.assist.start_scenario("operator-entry", {})
    finally:
        host.shutdown()


def test_assist_start_scenario_refused_when_dna_refuse() -> None:
    reset_system_log_for_tests()
    # all_in_one composition exposes server surfaces; embedded DNA refuses them
    host = ApplicationHost.for_mode("all_in_one", settings=_settings())
    host.start(structure_definition_id="local.embedded")
    try:
        assert host.assist is not None
        assert host.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            host.assist.start_scenario("operator-entry", {})
    finally:
        host.shutdown()


def test_assist_menu_nests_admission_when_closed() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("all_in_one", settings=_settings())
    host.start(structure_skip=True)
    try:
        assert host.assist is not None
        page = menu_for_assist(host.assist, section="root")
        assert page["start_allowed"] is False
        assert page["admission"]["may_run_business"] is False
        aliases = {a.get("alias") for a in page["actions"] if isinstance(a, dict)}
        assert "operator-entry/start" not in aliases
        assert "assist/top" in aliases
        assert "admission closed" in page["question"].lower() or "starts refuse" in page[
            "question"
        ].lower()
    finally:
        host.shutdown()


def test_assist_menu_start_allowed_when_admitted() -> None:
    reset_system_log_for_tests()
    # cli DNA matches no-surface membership without refuse dual
    host = ApplicationHost.for_mode("cli", settings=_settings())
    host.start()
    try:
        assert host.assist is not None
        assert host.admission.may_run_business is True
        page = menu_for_assist(host.assist, section="root")
        assert page["start_allowed"] is True
        assert page["admission"]["may_run_business"] is True
        aliases = {a.get("alias") for a in page["actions"] if isinstance(a, dict)}
        assert "operator-entry/start" in aliases
    finally:
        host.shutdown()


def test_build_menu_page_without_admission_defaults_start_allowed() -> None:
    page = build_menu_page(section="root", items=[], title="t")
    assert page["start_allowed"] is True
    assert "admission" not in page
