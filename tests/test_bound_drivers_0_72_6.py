"""0.72.6 — start receives bound drivers.

The kernel does not import a storage or a runner, and it does not default one.
The bundle binds storage before start.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from drivers.storages.memory import MemoryBackend

from palm.system.bound import BOUND_DRIVERS_VERSION, BoundDrivers
from palm.system.runtime.base import BaseRuntime

_REPO = Path(__file__).resolve().parents[1]


def _open_memory() -> MemoryBackend:
    from drivers.storages.load import open_backend

    backend = open_backend("memory")
    assert isinstance(backend, MemoryBackend)
    return backend


def _run_cold(body: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src = str(_REPO / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-c", body],
        capture_output=True,
        text=True,
        check=False,
        cwd=_REPO,
        env=env,
    )


def test_kernel_driver_guard() -> None:
    guard = subprocess.run(
        [sys.executable, str(_REPO / "scripts" / "guard_kernel_drivers.py")],
        capture_output=True,
        text=True,
        check=False,
        cwd=_REPO,
    )
    assert guard.returncode == 0, guard.stdout or guard.stderr
    assert "does not import drivers" in guard.stdout


def test_start_without_bound_drivers_fails_before_the_schedule() -> None:
    runtime = BaseRuntime()
    with pytest.raises(RuntimeError, match="requires bound drivers"):
        runtime.start()
    assert runtime.is_started is False
    assert runtime.last_boot_walk is None


def test_start_rejects_a_storage_name_in_place_of_bound_drivers() -> None:
    runtime = BaseRuntime()
    with pytest.raises(RuntimeError, match="refused storage_backend"):
        runtime.start(storage_backend="memory")
    assert runtime.is_started is False
    assert runtime.last_boot_walk is None


def test_start_rejects_a_contract_version_mismatch_before_the_schedule() -> None:
    runtime = BaseRuntime()
    drivers = BoundDrivers(version=2, storage=_open_memory(), workload_runtime=None)
    with pytest.raises(RuntimeError, match="contract version"):
        runtime.start(drivers=drivers, structure_definition_id="local.embedded")
    assert runtime.is_started is False
    assert runtime.last_boot_walk is None


def test_start_rejects_a_closed_storage_backend() -> None:
    runtime = BaseRuntime()
    drivers = BoundDrivers(
        version=BOUND_DRIVERS_VERSION,
        storage=MemoryBackend(),
        workload_runtime=None,
    )
    with pytest.raises(RuntimeError, match="not initialized"):
        runtime.start(drivers=drivers)
    assert runtime.is_started is False
    assert runtime.last_boot_walk is None


def test_empty_workload_slot_still_walks_local_embedded() -> None:
    runtime = BaseRuntime()
    storage = _open_memory()
    drivers = BoundDrivers(
        version=BOUND_DRIVERS_VERSION,
        storage=storage,
        workload_runtime=None,
    )
    runtime.start(drivers=drivers, structure_definition_id="local.embedded")
    try:
        assert runtime.is_started is True
        assert runtime.storage.backend is storage
        assert runtime.storage.backend_name == "memory"
        assert runtime.workload.is_initialized is True
        assert runtime.workload._default_runtime is None
        assert runtime.workload._runtimes == {}
        walked = [step.phase for step in (runtime.last_boot_walk or [])]
        assert "system.storage.select" in walked
        assert "system.engines.init" in walked
        assert walked[-1] == "system.background.start" or "system.ready" in walked
        assert runtime.structure is not None
        assert runtime.structure.definition is not None
        assert runtime.structure.definition.id == "local.embedded"
    finally:
        runtime.stop()


def test_cold_start_does_not_import_drivers() -> None:
    result = _run_cold(
        """
import sys

from palm.system.runtime.base import BaseRuntime

def driver_modules():
    return {
        name
        for name in sys.modules
        if name == "drivers" or name.startswith("drivers.")
    }

before = driver_modules()
runtime = BaseRuntime()
try:
    runtime.start()
    raise SystemExit("start without bound drivers returned")
except RuntimeError as exc:
    if "bound drivers" not in str(exc):
        raise
added = sorted(driver_modules() - before)
if added:
    raise SystemExit(f"start imported {added}")
if runtime.is_started:
    raise SystemExit("runtime started")
print("ok")
"""
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_minimal_bind_then_start_imports_no_further_drivers() -> None:
    result = _run_cold(
        """
import sys

from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime

bound = bind_memory()
assert bound.workload_runtime is None
assert bound.storage.name == "memory"
assert "drivers.storages.memory" in sys.modules
assert "drivers.runners" not in sys.modules

def driver_modules():
    return {
        name
        for name in sys.modules
        if name == "drivers" or name.startswith("drivers.")
    }

before = driver_modules()
runtime = MinimalRuntime()
runtime.start(drivers=bound, structure_definition_id="local.embedded")
try:
    added = sorted(driver_modules() - before)
    assert added == [], added
    assert runtime.is_started
    assert runtime.storage.backend is bound.storage
    assert runtime.workload._default_runtime is None
finally:
    runtime.stop()
print("ok")
"""
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "ok" in result.stdout


def test_standard_binds_the_storage_the_profile_names() -> None:
    from bundles.standard.app.host.application_host import ApplicationHost
    from bundles.standard.app.host.composition import CORE_SERVICES, CompositionProfile
    from bundles.standard.app.host.roles import DeploymentProfile
    from bundles.standard.app.settings import PalmSettings

    profile = CompositionProfile(
        services=CORE_SERVICES,
        surfaces=(),
        capabilities=frozenset(),
        kits=(),
        patterns=(),
        providers=(),
        runners=("local",),
        storages=("memory",),
        transforms=(),
    )
    host = ApplicationHost(
        PalmSettings(load_example_definitions=False, storage_backend="memory"),
        profile=DeploymentProfile.master_only(),
        composition=profile,
    )
    host.start()
    try:
        runtime = host.app.runtime()
        assert runtime.storage.backend_name == "memory"
        assert runtime.storage.backend is not None
        assert runtime.storage.backend.is_open
        names = set(runtime.workload._runtimes)
        assert "local" in names
        assert "host" not in names
        assert runtime.workload._default_runtime == "local"
    finally:
        host.shutdown()


def test_standard_rejects_a_storage_the_profile_does_not_name() -> None:
    from bundles.standard.app.host.application_host import ApplicationHost
    from bundles.standard.app.host.composition import CORE_SERVICES, CompositionProfile
    from bundles.standard.app.host.roles import DeploymentProfile
    from bundles.standard.app.settings import PalmSettings

    profile = CompositionProfile(
        services=CORE_SERVICES,
        surfaces=(),
        capabilities=frozenset(),
        kits=(),
        patterns=(),
        providers=(),
        runners=("local",),
        storages=("memory",),
        transforms=(),
    )
    host = ApplicationHost(
        PalmSettings(load_example_definitions=False, storage_backend="filesystem"),
        profile=DeploymentProfile.master_only(),
        composition=profile,
    )
    with pytest.raises(RuntimeError, match="not a storage the profile names"):
        host.start()
    assert host.is_started is False
