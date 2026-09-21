"""0.71.17 — embedded import must not load server (or sibling) surface packages."""

from __future__ import annotations

import subprocess
import sys
import textwrap


def _run_isolation_script(body: str) -> subprocess.CompletedProcess[str]:
    script = textwrap.dedent(body).strip() + "\n"
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )


def test_embedded_import_does_not_load_sibling_surfaces() -> None:
    result = _run_isolation_script(
        """
        import sys

        from palm.runtimes.embedded import EmbeddedRuntime

        assert EmbeddedRuntime is not None
        for name in (
            "palm.runtimes.server",
            "palm.runtimes.daemon",
            "palm.runtimes.mcp",
            "palm.runtimes.cli",
        ):
            assert name not in sys.modules, f"unexpected load: {name}"
            assert not any(
                key == name or key.startswith(name + ".") for key in sys.modules
            ), f"unexpected subtree: {name}"
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_palm_kernel_embedded_start_does_not_load_server() -> None:
    result = _run_isolation_script(
        """
        import sys

        from palm.app.bootstrap import ensure_plugins

        ensure_plugins()
        from palm.app import PalmKernel, PalmSettings

        app = PalmKernel(PalmSettings(load_example_definitions=False))
        app.bootstrap()
        runtime = app.create_runtime("embedded", autostart=True)
        assert runtime.is_started
        assert "palm.runtimes.server" not in sys.modules
        assert not any(
            key == "palm.runtimes.server" or key.startswith("palm.runtimes.server.")
            for key in sys.modules
        )
        assert "palm.runtimes.daemon" not in sys.modules
        assert "palm.runtimes.mcp" not in sys.modules
        runtime.stop()
        app.shutdown()
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_server_still_imports_from_server_package() -> None:
    result = _run_isolation_script(
        """
        from palm.runtimes.server import ServerRuntime, run_server

        assert ServerRuntime is not None
        assert callable(run_server)
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_runtimes_package_init_has_no_sibling_surface_imports() -> None:
    import ast
    from pathlib import Path

    tree = ast.parse(Path("src/palm/runtimes/__init__.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
            for alias in node.names:
                imported.add(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    for sibling in ("daemon", "embedded", "server", "mcp", "cli"):
        assert f"palm.runtimes.{sibling}" not in imported
