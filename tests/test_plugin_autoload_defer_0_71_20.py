"""0.71.20 — pattern/provider autoload at bootstrap, not package import."""

from __future__ import annotations

import subprocess
import sys
import textwrap


def _run_cold_script(body: str) -> subprocess.CompletedProcess[str]:
    script = textwrap.dedent(body).strip() + "\n"
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )


def test_import_palm_patterns_does_not_autoload_installed_members() -> None:
    result = _run_cold_script(
        """
        import sys

        from palm.patterns._apps import INSTALLED_PATTERNS
        import palm.patterns

        assert palm.patterns.INSTALLED_PATTERNS == INSTALLED_PATTERNS
        for name in INSTALLED_PATTERNS:
            mod = f"palm.patterns.{name}"
            assert mod not in sys.modules, f"unexpected load: {mod}"
            assert not any(
                key == mod or key.startswith(mod + ".") for key in sys.modules
            ), f"unexpected subtree: {mod}"
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_import_palm_providers_does_not_autoload_installed_members() -> None:
    result = _run_cold_script(
        """
        import sys

        from palm.providers._apps import INSTALLED_PROVIDERS
        import palm.providers

        assert palm.providers.INSTALLED_PROVIDERS == INSTALLED_PROVIDERS
        for name in INSTALLED_PROVIDERS:
            mod = f"palm.providers.{name}"
            assert mod not in sys.modules, f"unexpected load: {mod}"
            assert not any(
                key == mod or key.startswith(mod + ".") for key in sys.modules
            ), f"unexpected subtree: {mod}"
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_application_host_cold_import_skips_bulk_pattern_members() -> None:
    """Wizard may still load via ApplicationHost; other INSTALLED patterns must not."""
    result = _run_cold_script(
        """
        import sys

        from palm.app import ApplicationHost

        assert ApplicationHost.__name__ == "ApplicationHost"
        for name in ("dag", "parallel", "pipeline"):
            mod = f"palm.patterns.{name}"
            assert mod not in sys.modules, f"unexpected load: {mod}"
            assert not any(
                key == mod or key.startswith(mod + ".") for key in sys.modules
            ), f"unexpected subtree: {mod}"
        for name in ("rest", "palm", "kv", "file", "authoring"):
            mod = f"palm.providers.{name}"
            assert mod not in sys.modules, f"unexpected load: {mod}"
            assert not any(
                key == mod or key.startswith(mod + ".") for key in sys.modules
            ), f"unexpected subtree: {mod}"
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_ensure_core_plugins_loads_patterns_and_providers() -> None:
    result = _run_cold_script(
        """
        from palm.common.plugins import ensure_core_plugins
        from palm.core.registry import pattern_registry, provider_registry
        from palm.patterns._apps import INSTALLED_PATTERNS
        from palm.providers._apps import INSTALLED_PROVIDERS

        ensure_core_plugins()

        for name in INSTALLED_PATTERNS:
            pattern_registry.get(name)
        for name in INSTALLED_PROVIDERS:
            provider_registry.get(name)
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_host_start_registers_patterns_and_providers() -> None:
    result = _run_cold_script(
        """
        from palm.app import ApplicationHost
        from palm.app.settings import PalmSettings
        from palm.core.registry import pattern_registry, provider_registry
        from palm.patterns._apps import INSTALLED_PATTERNS
        from palm.providers._apps import INSTALLED_PROVIDERS

        host = ApplicationHost(PalmSettings(load_example_definitions=False))
        host.start()
        try:
            for name in INSTALLED_PATTERNS:
                pattern_registry.get(name)
            for name in INSTALLED_PROVIDERS:
                provider_registry.get(name)
        finally:
            host.shutdown()
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout
