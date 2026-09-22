"""0.71.21 — ApplicationHost path must not load plugins.kits.server."""

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


def test_from_palm_app_import_application_host_skips_kits_server() -> None:
    result = _run_cold_script(
        """
        import sys

        from bundles.standard.app import ApplicationHost

        assert ApplicationHost.__name__ == "ApplicationHost"
        server_keys = sorted(
            key
            for key in sys.modules
            if key == "plugins.kits.server" or key.startswith("plugins.kits.server.")
        )
        assert not server_keys, f"unexpected kits.server load: {server_keys}"
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_embedded_application_host_start_skips_kits_server() -> None:
    result = _run_cold_script(
        """
        import sys

        from bundles.standard.app import ApplicationHost
        from bundles.standard.app.settings import PalmSettings

        host = ApplicationHost(PalmSettings(load_example_definitions=False))
        host.start()
        try:
            server_keys = sorted(
                key
                for key in sys.modules
                if key == "plugins.kits.server" or key.startswith("plugins.kits.server.")
            )
            assert not server_keys, f"unexpected kits.server load: {server_keys}"
        finally:
            host.shutdown()
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_server_start_still_wires_kits_server() -> None:
    result = _run_cold_script(
        """
        import sys

        from bundles.standard.app.bootstrap import ensure_plugins

        ensure_plugins()
        from bundles.standard.app.settings import PalmSettings
        from bundles.standard.runtimes.server.context import ServerContext
        from bundles.standard.runtimes.server.runtime import ServerRuntime

        runtime = ServerRuntime(host="127.0.0.1", port=0)
        runtime.start(http=False)
        try:
            ctx = ServerContext(
                runtime,
                host=None,
                settings=PalmSettings(load_example_definitions=False),
            )
            assert ctx.query_bus is not None
            assert "plugins.kits.server.cqrs" in sys.modules
        finally:
            runtime.stop()
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout
