"""0.66.2 — eyes show installed capabilities (not 3-key remain)."""

from __future__ import annotations

from types import SimpleNamespace

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import StructurePhase
from palm.services.assist.catalog.menu import menu_for_assist
from palm.services.inspect.present import present_top
from palm.system.log import reset_system_log_for_tests
from palm.system.structure import admission_as_dict
from palm.system.vitality import SEAT_STRUCTURE, walk_result
from palm.system.vitality.seats import reset_default_probe_catalog_for_tests


def _lean() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


def test_admission_as_dict_includes_capabilities_on_duck() -> None:
    duck = SimpleNamespace(
        may_run_business=True,
        phase=StructurePhase.READY,
        definition_id="local.cli",
        capabilities=["work_drain"],
    )
    bag = admission_as_dict(duck)
    assert bag is not None
    assert bag["capabilities"] == ["work_drain"]
    assert admission_as_dict(None) is None


def test_eyes_columns_on_cli_host() -> None:
    reset_system_log_for_tests()
    reset_default_probe_catalog_for_tests()
    host = ApplicationHost.for_mode(BootMode.cli(), settings=_lean())
    host.start()
    try:
        top = present_top(host.runtime())
        assert "work_drain" in top["admission"]["capabilities"]

        bag = host.packaging_status()["structure"]
        assert "work_drain" in bag["capabilities"]

        report = walk_result(host.runtime()).by_id()[SEAT_STRUCTURE]
        assert "work_drain" in report.load["capabilities"]

        if host.assist is not None:
            page = menu_for_assist(host.assist, section="root")
            assert "work_drain" in page["admission"]["capabilities"]
    finally:
        host.shutdown()


def test_embedded_eyes_publish_empty_capabilities() -> None:
    reset_system_log_for_tests()
    reset_default_probe_catalog_for_tests()
    host = ApplicationHost.for_mode(BootMode.safe(), settings=_lean())
    host.start()
    try:
        top = present_top(host.runtime())
        assert top["admission"]["capabilities"] == []
        assert host.packaging_status()["structure"]["capabilities"] == []
    finally:
        host.shutdown()
