"""Constrained start of bundles.minimal. The root conftest installs the fat package set.

The cold test runs a fresh interpreter so that latch is not in the process.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_MINIMAL = _REPO / "src" / "bundles" / "minimal"

_FORBIDDEN_PREFIXES = (
    "bundles.standard",
    "palm.common.plugins",
    "palm.services",
    "plugins.patterns",
    "plugins.providers",
    "plugins.kits",
    "plugins.runners",
)


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return found


def _forbidden(module: str) -> str | None:
    for prefix in _FORBIDDEN_PREFIXES:
        if module == prefix or module.startswith(prefix + "."):
            return prefix
    return None


def test_minimal_package_does_not_import_the_standard_bundle_or_plugin_stroke() -> None:
    offenders: list[str] = []
    for path in sorted(_MINIMAL.rglob("*.py")):
        for module in _imported_modules(path):
            prefix = _forbidden(module)
            if prefix is not None:
                offenders.append(f"{path.relative_to(_REPO)} imports {module}")
    assert offenders == []


def test_minimal_start_does_not_load_the_plugin_stroke() -> None:
    script = """
import sys

from bundles.minimal.app import MinimalApp

app = MinimalApp()
runtime = app.start()
try:
    assert runtime.is_started
    assert runtime.structure is not None
    assert runtime.structure.definition is not None
    assert runtime.structure.definition.id == "local.embedded"
    assert runtime.planes is not None
    banned = (
        "palm.common.plugins",
        "bundles.standard",
        "palm.services",
        "plugins.patterns",
        "plugins.providers",
        "plugins.kits",
        "plugins.runners",
    )
    loaded = [
        name
        for name in sys.modules
        if any(name == prefix or name.startswith(prefix + ".") for prefix in banned)
    ]
    assert loaded == [], loaded
    assert "plugins.storages.memory" in sys.modules
finally:
    app.stop()
print("ok")
"""
    env = os.environ.copy()
    src = str(_REPO / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
        cwd=_REPO,
        env=env,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout
