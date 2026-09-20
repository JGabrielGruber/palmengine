"""0.71.19 — bare ApplicationHost import must succeed in a cold interpreter."""

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


def test_from_palm_app_import_application_host_cold() -> None:
    """Public door: no ensure_core_plugins warm-up; no ImportError cycle."""
    result = _run_cold_script(
        """
        from palm.app import ApplicationHost

        assert ApplicationHost.__name__ == "ApplicationHost"
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_application_host_cold_import_without_ensure_core_plugins() -> None:
    """Same door without any prior ensure_core_plugins() call (cold process)."""
    result = _run_cold_script(
        """
        # Deliberately do not call ensure_core_plugins().
        from palm.app import ApplicationHost

        cls = ApplicationHost
        assert isinstance(cls, type)
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout
