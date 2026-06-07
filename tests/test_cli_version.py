"""CLI version command tests."""

from __future__ import annotations

import subprocess
import sys

from palm import __version__


def test_version_module() -> None:
    assert __version__ == "0.5.0-dev"


def test_cli_version_brief() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "palm.runtimes.cli", "version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "0.5.0-dev" in result.stdout


def test_cli_version_full() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "palm.runtimes.cli", "version", "--full"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "wizard" in result.stdout
    assert "0.5.0-dev" in result.stdout


def test_cli_help_lists_commands() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "palm.runtimes.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "doctor" in result.stdout
    assert "wizard" in result.stdout
    assert "full_demo.py" in result.stdout
    assert "SCOPE.md" in result.stdout
