"""Local WorkloadRuntime — always on, Palm-managed process runner."""

from __future__ import annotations

import sys

from palm.core.workload import (
    IsolationPolicy,
    LifecyclePolicy,
    WorkloadEngine,
    WorkloadKind,
    WorkloadPlacement,
    WorkloadSpec,
    WorkloadStatus,
)
from plugins.runners.local.runtime import LocalWorkloadRuntime


def test_local_always_enabled_and_healthy(tmp_path) -> None:
    rt = LocalWorkloadRuntime(work_root=tmp_path)
    assert rt.is_enabled() is True
    h = rt.health()
    assert h.available is True
    assert h.enabled is True
    assert rt.capabilities().trust == "local"
    assert rt.capabilities().default_enabled is True


def test_local_run_python(tmp_path) -> None:
    engine = WorkloadEngine()
    engine.initialize(
        runtimes={"local": LocalWorkloadRuntime(work_root=tmp_path)},
        default_runtime="local",
    )
    wl = engine.start(
        WorkloadSpec(
            kind=WorkloadKind.RUN,
            isolation=IsolationPolicy.BEST_EFFORT,
            lifecycle=LifecyclePolicy.JOB,
            command=(sys.executable, "-c", "print('local-ok')"),
            placement=WorkloadPlacement(runtime="local"),
        )
    )
    assert wl.status is WorkloadStatus.STOPPED
    assert wl.result is not None and wl.result.success
    assert "local-ok" in wl.result.stdout_tail
    engine.shutdown()


def test_local_rejects_hermetic() -> None:
    import pytest

    from palm.core.workload import WorkloadPolicyError

    engine = WorkloadEngine()
    engine.initialize(runtimes={"local": LocalWorkloadRuntime()})
    with pytest.raises(WorkloadPolicyError, match="hermetic"):
        engine.start(
            WorkloadSpec(
                kind=WorkloadKind.RUN,
                isolation=IsolationPolicy.HERMETIC,
                lifecycle=LifecyclePolicy.JOB,
                command=("true",),
                placement=WorkloadPlacement(runtime="local"),
            )
        )
    engine.shutdown()


def test_engine_doctor_includes_health(tmp_path) -> None:
    engine = WorkloadEngine()
    engine.initialize(
        runtimes={"local": LocalWorkloadRuntime(work_root=tmp_path)},
        default_runtime="local",
    )
    doc = engine.doctor()
    assert doc["engine_initialized"] is True
    assert doc["default_runtime"] == "local"
    names = {r["name"] for r in doc["runtimes"]}
    assert "local" in names
    local = next(r for r in doc["runtimes"] if r["name"] == "local")
    assert local["health"]["available"] is True
    assert local["enabled"] is True
    engine.shutdown()


def test_bootstrap_default_local(tmp_path) -> None:
    from palm.system.subsystems.planes.workload.bootstrap import initialize_workload_engine

    engine = WorkloadEngine()
    initialize_workload_engine(engine, work_root=tmp_path)
    assert engine._default_runtime == "local"
    assert "local" in engine._runtimes
    assert engine._runtimes["local"].is_enabled()
    assert engine._runtimes["host"].is_enabled() is False
    engine.shutdown()
