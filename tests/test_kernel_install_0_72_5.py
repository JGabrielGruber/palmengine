"""0.72.5 — the kernel schedule has no install phase.

The standard bundle installs once, in kernel bootstrap, before system start.
``start`` refuses ``plugin_install`` and ``composition_packages``.
Storage select may still import ``drivers.storages`` (0.72.6).
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from palm.system.boot import system_phase_ids
from palm.system.runtime.base import BaseRuntime

_REPO = Path(__file__).resolve().parents[1]


def _run_cold(body: str) -> subprocess.CompletedProcess[str]:
    script = textwrap.dedent(body).strip() + "\n"
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
        cwd=_REPO,
    )


def test_system_schedule_has_no_install_phase() -> None:
    assert "system.plugins.ensure" not in system_phase_ids()
    assert system_phase_ids()[0] == "system.log.ready"
    assert system_phase_ids()[1] == "system.engines.init"
    guard = subprocess.run(
        [sys.executable, str(_REPO / "scripts" / "guard_kernel_install.py")],
        capture_output=True,
        text=True,
        check=False,
        cwd=_REPO,
    )
    assert guard.returncode == 0, guard.stdout or guard.stderr


def test_start_refuses_install_keys() -> None:
    runtime = BaseRuntime()
    with pytest.raises(RuntimeError, match="does not install"):
        runtime.start(storage_backend="memory", plugin_install=lambda **_kwargs: None)
    assert runtime.is_started is False
    with pytest.raises(RuntimeError, match="does not install"):
        runtime.start(storage_backend="memory", composition_packages={})
    assert runtime.is_started is False


def test_standard_host_installs_before_engines_init() -> None:
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
            walked = [step.phase for step in host._app.runtime().last_boot_walk]
            assert "system.plugins.ensure" not in walked
            assert walked[0] == "system.log.ready"
            assert "system.engines.init" in walked
            assert "plugins.kits.present" in sys.modules
            assert "plugins.kits.authoring" not in sys.modules
            assert "drivers.runners.local" in sys.modules
            assert "drivers.runners.host" not in sys.modules
        finally:
            host.shutdown()
        print("ok")
        """
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout
