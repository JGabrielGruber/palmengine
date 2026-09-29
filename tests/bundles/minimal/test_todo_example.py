"""Todo example on MinimalApp, and the withdrawn catalog install.

The behavior probe runs in a fresh interpreter, the same way
``python examples/todo/main.py`` imports ``todo_engine``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]


def _python(script: str, *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src = str(_REPO / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd or _REPO,
        env=env,
    )


def test_catalog_autoload_refuses_and_does_not_import() -> None:
    script = """
import sys
from plugins.patterns import autoload

try:
    autoload(("wizard",))
except RuntimeError as exc:
    assert "withdrawn" in str(exc)
else:
    raise SystemExit("autoload returned")
assert "plugins.patterns.wizard" not in sys.modules
print("ok")
"""
    result = _python(script)
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_standard_bootstrap_refuses_catalog_install() -> None:
    script = """
from bundles.standard.app.kernel import PalmKernel

try:
    PalmKernel().bootstrap()
except RuntimeError as exc:
    assert "withdrawn" in str(exc)
else:
    raise SystemExit("bootstrap returned")
print("ok")
"""
    result = _python(script)
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_todo_example_lists_adds_and_toggles_on_minimal_app() -> None:
    script = """
import sys
from todo_engine import TodoEngine

from palm.core.registry import pattern_registry, provider_registry

assert "wizard" not in pattern_registry.names()
assert "kv" not in provider_registry.names()
engine = TodoEngine()
engine.start()
assert "wizard" in pattern_registry.names()
assert "kv" in provider_registry.names()
try:
    assert engine.list_todos() == []
    item = engine.add_todo("milk")
    listed = engine.list_todos()
    assert [row.title for row in listed] == ["milk"]
    toggled = engine.toggle_todo(item.id, True)
    assert toggled.done is True
    assert engine.list_todos()[0].done is True
    loaded = sys.modules
    assert "plugins.patterns.wizard" in loaded
    assert "plugins.providers.kv" in loaded
    banned = (
        "plugins.patterns.dag",
        "plugins.providers.rest",
        "plugins.kits.present",
        "drivers.runners.local",
        "bundles.standard.app.host.application_host",
    )
    present = [name for name in banned if name in loaded]
    assert present == [], present
finally:
    engine.shutdown()
print("ok")
"""
    result = _python(script, cwd=_REPO / "examples" / "todo")
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_ensure_plugins_refuses_in_process() -> None:
    from bundles.standard.app.bootstrap import ensure_plugins

    with pytest.raises(RuntimeError, match="withdrawn"):
        ensure_plugins()
