"""Host WorkloadRuntime — default OFF, hermetic rejection, subprocess run."""

from __future__ import annotations

import sys

import pytest

from palm.core.workload import (
    IsolationPolicy,
    LifecyclePolicy,
    WorkloadEngine,
    WorkloadKind,
    WorkloadOwner,
    WorkloadPlacement,
    WorkloadPolicyError,
    WorkloadSpec,
    WorkloadStatus,
)
from plugins.runners.host.runtime import HostWorkloadRuntime


def _run_spec(*, runtime: str = "host", isolation: IsolationPolicy = IsolationPolicy.HOST) -> WorkloadSpec:
    return WorkloadSpec(
        kind=WorkloadKind.RUN,
        isolation=isolation,
        lifecycle=LifecyclePolicy.JOB,
        command=(sys.executable, "-c", "print('host-ok')"),
        placement=WorkloadPlacement(runtime=runtime),
    )


def test_host_disabled_by_default_engine_policy() -> None:
    rt = HostWorkloadRuntime(enabled=False)
    engine = WorkloadEngine()
    engine.initialize(runtimes={"host": rt})
    with pytest.raises(WorkloadPolicyError, match="disabled"):
        engine.start(_run_spec())
    engine.shutdown()


def test_host_enabled_runs_subprocess() -> None:
    rt = HostWorkloadRuntime(enabled=True)
    engine = WorkloadEngine()
    engine.initialize(runtimes={"host": rt})
    wl = engine.start(_run_spec(), owner=WorkloadOwner(job_id="j1"))
    assert wl.status is WorkloadStatus.STOPPED
    assert wl.result is not None
    assert wl.result.success
    assert "host-ok" in (wl.result.stdout_tail or "")
    engine.shutdown()


def test_host_non_zero_exit_is_failed() -> None:
    rt = HostWorkloadRuntime(enabled=True)
    engine = WorkloadEngine()
    engine.initialize(runtimes={"host": rt})
    spec = WorkloadSpec(
        kind=WorkloadKind.RUN,
        isolation=IsolationPolicy.HOST,
        lifecycle=LifecyclePolicy.JOB,
        command=(sys.executable, "-c", "raise SystemExit(3)"),
        placement=WorkloadPlacement(runtime="host"),
    )
    wl = engine.start(spec)
    assert wl.status is WorkloadStatus.FAILED
    assert wl.result is not None
    assert wl.result.exit_code == 3
    engine.shutdown()


def test_hermetic_cannot_select_host() -> None:
    rt = HostWorkloadRuntime(enabled=True)
    engine = WorkloadEngine()
    engine.initialize(runtimes={"host": rt})
    with pytest.raises(WorkloadPolicyError, match="[Hh]ermetic|host"):
        engine.start(
            WorkloadSpec(
                kind=WorkloadKind.RUN,
                isolation=IsolationPolicy.HERMETIC,
                lifecycle=LifecyclePolicy.JOB,
                command=(sys.executable, "-c", "print(1)"),
                placement=WorkloadPlacement(runtime="host"),
            )
        )
    engine.shutdown()


def test_host_doctor_warns_when_enabled() -> None:
    on = WorkloadEngine()
    on.initialize(runtimes={"host": HostWorkloadRuntime(enabled=True)})
    try:
        issues = on.doctor()["issues"]
        assert any("ENABLED" in i for i in issues)
    finally:
        on.shutdown()

    off = WorkloadEngine()
    off.initialize(runtimes={"host": HostWorkloadRuntime(enabled=False)})
    try:
        issues = off.doctor()["issues"]
        assert not any("host WorkloadRuntime is ENABLED" in i for i in issues)
    finally:
        off.shutdown()


def test_host_workspace_ready_and_exec() -> None:
    rt = HostWorkloadRuntime(enabled=True)
    engine = WorkloadEngine()
    engine.initialize(runtimes={"host": rt})
    wl = engine.start(
        WorkloadSpec(
            kind=WorkloadKind.WORKSPACE,
            isolation=IsolationPolicy.HOST,
            lifecycle=LifecyclePolicy.SESSION,
            placement=WorkloadPlacement(runtime="host"),
        )
    )
    assert wl.status is WorkloadStatus.READY
    assert wl.handle is not None
    result = engine.exec(
        wl.workload_id,
        [sys.executable, "-c", "print('ws')"],
    )
    assert result.success
    assert "ws" in result.stdout_tail
    stopped = engine.stop(wl.workload_id)
    assert stopped.status is WorkloadStatus.STOPPED
    engine.shutdown()
