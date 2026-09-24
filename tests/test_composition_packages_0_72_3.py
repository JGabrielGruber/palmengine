"""0.72.3 — package names on the composition record, one install stroke.

The stroke walks those names. CORE_KITS, runner host always-import, and
include_optional are not the membership law. Every saved record names the
same set in this slice. Measure stays not pass.
"""

from __future__ import annotations

import inspect
import subprocess
import sys
import textwrap

import pytest
from bundles.standard.app.bootstrap import composition_profile_from_settings
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.host.composition import (
    COMPOSITION_RECORDS,
    RECORD_KITS,
    RECORD_PATTERNS,
    RECORD_PROVIDERS,
    RECORD_RUNNERS,
    RECORD_STORAGES,
    RECORD_TRANSFORMS,
    CompositionProfile,
    composition_profile_from_name,
    composition_record,
)
from bundles.standard.app.settings import PalmSettings
from plugins.storages._apps import autoload as autoload_storages

_FAMILIES = ("kits", "patterns", "providers", "runners", "storages", "transforms")


def _run_cold(body: str) -> subprocess.CompletedProcess[str]:
    script = textwrap.dedent(body).strip() + "\n"
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )


def test_saved_records_name_package_families() -> None:
    expected = {
        "kits": RECORD_KITS,
        "patterns": RECORD_PATTERNS,
        "providers": RECORD_PROVIDERS,
        "runners": RECORD_RUNNERS,
        "storages": RECORD_STORAGES,
        "transforms": RECORD_TRANSFORMS,
    }
    for row in COMPOSITION_RECORDS:
        for family, names in expected.items():
            assert getattr(row, family) == names
        assert "server" not in row.kits
        assert "host" in row.runners
        assert "postgres" not in row.storages
        assert "mongodb" not in row.storages


def test_from_record_copies_package_names() -> None:
    profile = composition_profile_from_name("embedded")
    record = composition_record("embedded")
    assert profile.package_names() == {
        "kits": tuple(record.kits),
        "patterns": tuple(record.patterns),
        "providers": tuple(record.providers),
        "runners": tuple(record.runners),
        "storages": tuple(record.storages),
        "transforms": tuple(record.transforms),
    }
    assert BootMode.safe().composition.kits == record.kits
    assert BootMode.worker().composition.runners == record.runners


def test_settings_resolver_copies_package_names() -> None:
    record = composition_record("all_in_one")
    profile = composition_profile_from_settings(PalmSettings.for_tests(load_examples=False))
    assert profile.kits == record.kits
    assert profile.patterns == record.patterns
    assert profile.providers == record.providers
    assert profile.runners == record.runners
    assert profile.storages == record.storages
    assert profile.transforms == record.transforms


def test_core_kits_is_not_the_walk_law() -> None:
    import plugins.kits as kits

    assert not hasattr(kits, "CORE_KITS")


def test_storage_autoload_has_no_include_optional() -> None:
    assert "include_optional" not in inspect.signature(autoload_storages).parameters
    assert list(inspect.signature(autoload_storages).parameters) == ["names"]


@pytest.mark.parametrize("family", _FAMILIES)
def test_profile_package_fields_match_the_record(family: str) -> None:
    profile = CompositionProfile.from_record(composition_record("cli"))
    assert getattr(profile, family) == getattr(composition_record("cli"), family)


def test_stroke_walks_the_given_names_and_a_later_call_can_add() -> None:
    result = _run_cold(
        """
        import sys

        from palm.common.plugins import ensure_core_plugins

        ensure_core_plugins(
            kits=("present",),
            patterns=(),
            providers=(),
            runners=("local",),
            storages=("memory",),
            transforms=(),
        )
        assert "plugins.kits.present" in sys.modules
        assert "plugins.kits.authoring" not in sys.modules
        assert "plugins.runners.host" not in sys.modules
        assert "plugins.runners.local" in sys.modules
        assert "plugins.storages.postgres" not in sys.modules

        ensure_core_plugins(
            kits=("present", "authoring"),
            patterns=(),
            providers=(),
            runners=("local", "host"),
            storages=("memory",),
            transforms=(),
        )
        assert "plugins.kits.authoring" in sys.modules
        assert "plugins.runners.host" in sys.modules
        assert "plugins.kits.server" not in sys.modules
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_phase_installs_only_the_option_set() -> None:
    result = _run_cold(
        """
        import sys

        from palm.system.boot.context import BootContext
        from palm.system.runtime.phase_plugins import run

        run(BootContext(schedule="system"), {})
        assert "palm.common.plugins" not in sys.modules
        assert "plugins.runners.local" not in sys.modules
        assert "plugins.kits.present" not in sys.modules

        from palm.common.plugins import ensure_core_plugins

        def install() -> None:
            ensure_core_plugins(
                kits=("present",),
                patterns=(),
                providers=(),
                runners=("local",),
                storages=("memory",),
                transforms=(),
            )

        run(BootContext(schedule="system"), {"plugin_install": install})
        assert "plugins.kits.present" in sys.modules
        assert "plugins.runners.local" in sys.modules
        assert "plugins.runners.host" not in sys.modules
        assert "plugins.kits.authoring" not in sys.modules
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_host_start_installs_the_composition_set() -> None:
    result = _run_cold(
        """
        import sys

        from bundles.standard.app.host.application_host import ApplicationHost
        from bundles.standard.app.host.composition import CORE_SERVICES, CompositionProfile
        from bundles.standard.app.host.roles import DeploymentProfile
        from bundles.standard.app.settings import PalmSettings

        profile = CompositionProfile(
            services=CORE_SERVICES,
            surfaces=(),
            capabilities=frozenset(),
            kits=("present",),
            patterns=("wizard",),
            providers=("palm",),
            runners=("local",),
            storages=("memory",),
        )
        host = ApplicationHost(
            PalmSettings(load_example_definitions=False),
            profile=DeploymentProfile.master_only(),
            composition=profile,
        )
        host.start()
        try:
            assert "plugins.kits.present" in sys.modules
            assert "plugins.kits.authoring" not in sys.modules
            assert "plugins.kits.server" not in sys.modules
            assert "plugins.runners.local" in sys.modules
            assert "plugins.runners.host" not in sys.modules
            assert "plugins.storages.postgres" not in sys.modules
        finally:
            host.shutdown()
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_saved_embedded_record_still_names_host_and_authoring() -> None:
    """Same set on embedded. A smaller embed set is a later measure."""
    result = _run_cold(
        """
        import sys

        from bundles.standard.app.host.application_host import ApplicationHost
        from bundles.standard.app.host.composition import composition_profile_from_name
        from bundles.standard.app.host.roles import DeploymentProfile
        from bundles.standard.app.settings import PalmSettings

        profile = composition_profile_from_name("embedded")
        host = ApplicationHost(
            PalmSettings(load_example_definitions=False),
            profile=DeploymentProfile.master_only(),
            composition=profile,
        )
        host.start()
        try:
            assert "plugins.kits.authoring" in sys.modules
            assert "plugins.runners.host" in sys.modules
            assert "plugins.kits.server" not in sys.modules
            assert "plugins.storages.postgres" not in sys.modules
        finally:
            host.shutdown()
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout
