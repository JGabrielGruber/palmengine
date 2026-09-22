"""0.72.4 — second menus follow the composition record.

Transform names are on the record. The install stroke walks them.
Service names stay the phenotype tuple. The host imports that tuple.
``INSTALLED_TRANSFORMS`` and ``INSTALLED_SERVICES`` stay catalogs.
Every saved record names the same transform set. Measure stays not pass.
"""

from __future__ import annotations

import inspect
import subprocess
import sys
import textwrap

from bundles.standard.app.host.composition import (
    COMPOSITION_RECORDS,
    RECORD_TRANSFORMS,
    CompositionProfile,
    composition_record,
)
from palm.common.transforms._apps import INSTALLED_TRANSFORMS, autoload as autoload_transforms
from palm.services._apps import INSTALLED_SERVICES, autoload as autoload_services


def _run_cold(body: str) -> subprocess.CompletedProcess[str]:
    script = textwrap.dedent(body).strip() + "\n"
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )


def test_saved_records_name_the_same_transform_set() -> None:
    assert RECORD_TRANSFORMS == INSTALLED_TRANSFORMS
    assert "parquet_load" not in RECORD_TRANSFORMS
    for row in COMPOSITION_RECORDS:
        assert row.transforms == RECORD_TRANSFORMS
    profile = CompositionProfile.from_record(composition_record("embedded"))
    assert profile.transforms == RECORD_TRANSFORMS
    assert profile.services != composition_record("all_in_one").services


def test_transform_autoload_takes_names() -> None:
    assert list(inspect.signature(autoload_transforms).parameters) == ["names"]


def test_service_autoload_takes_names() -> None:
    assert list(inspect.signature(autoload_services).parameters) == ["names"]
    assert "analytics" not in INSTALLED_SERVICES


def test_importing_transforms_does_not_register_rules() -> None:
    result = _run_cold(
        """
        import palm.common.transforms
        from palm.core.transform.registry import transform_registry

        assert transform_registry.names() == []
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_stroke_registers_only_the_named_transforms() -> None:
    result = _run_cold(
        """
        from palm.common.plugins import ensure_core_plugins
        from palm.core.transform.registry import transform_registry

        ensure_core_plugins(
            kits=(),
            patterns=(),
            providers=(),
            runners=(),
            storages=(),
            transforms=("rename_field",),
        )
        assert transform_registry.names() == ["rename_field"]
        assert "parquet_load" not in transform_registry.names()

        ensure_core_plugins(
            kits=(),
            patterns=(),
            providers=(),
            runners=(),
            storages=(),
            transforms=("rename_field", "calculate"),
        )
        assert transform_registry.names() == ["calculate", "rename_field"]
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_host_imports_the_record_service_names() -> None:
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
            transforms=(),
        )
        host = ApplicationHost(
            PalmSettings(load_example_definitions=False),
            profile=DeploymentProfile.master_only(),
            composition=profile,
        )
        host.start()
        try:
            assert "palm.services.inspect" in sys.modules
            assert "palm.services.execution" in sys.modules
            assert "palm.services.assist" not in sys.modules
        finally:
            host.shutdown()

        profile_full = CompositionProfile(
            services=CORE_SERVICES + ("assist",),
            surfaces=(),
            capabilities=frozenset(),
            kits=("present",),
            patterns=("wizard",),
            providers=("palm",),
            runners=("local",),
            storages=("memory",),
            transforms=(),
        )
        host_full = ApplicationHost(
            PalmSettings(load_example_definitions=False),
            profile=DeploymentProfile.master_only(),
            composition=profile_full,
        )
        host_full.start()
        try:
            assert "palm.services.assist" in sys.modules
        finally:
            host_full.shutdown()
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout
