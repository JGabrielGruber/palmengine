"""BaseRuntime wires WorkloadEngine; host default OFF; doctor surface."""

from __future__ import annotations

from bundles.standard.app.bootstrap import runtime_start_options
from bundles.standard.app.settings import PalmSettings
from plugins.kits.server.diagnostics import build_doctor_report
from palm.core.workload import (
    IsolationPolicy,
    LifecyclePolicy,
    WorkloadKind,
    WorkloadPlacement,
    WorkloadPolicyError,
    WorkloadSpec,
)
from bundles.standard.runtimes.embedded import EmbeddedRuntime


def test_embedded_runtime_wires_workload_engine() -> None:
    rt = EmbeddedRuntime()
    rt.start(storage_backend="memory")
    try:
        assert rt.workload.is_initialized
        names = {row["name"] for row in rt.workload.runtimes()}
        assert "local" in names
        assert "host" in names
        assert "neonroot" in names
        assert rt.workload._runtimes["local"].is_enabled() is True
        # host instance must be disabled
        host = rt.workload._runtimes["host"]
        assert host.is_enabled() is False
        doc = rt.workload.doctor()
        assert doc["default_runtime"] == "local"
        assert any(r.get("health") for r in doc["runtimes"] if r.get("name") == "local")
    finally:
        rt.stop()


def test_host_start_blocked_when_default_settings() -> None:
    rt = EmbeddedRuntime()
    opts = runtime_start_options(PalmSettings.for_tests())
    assert opts.get("workload_host_enabled") is False
    rt.start(**opts)
    try:
        with __import__("pytest").raises(WorkloadPolicyError, match="disabled"):
            rt.workload.start(
                WorkloadSpec(
                    kind=WorkloadKind.RUN,
                    isolation=IsolationPolicy.HOST,
                    lifecycle=LifecyclePolicy.JOB,
                    command=("true",),
                    placement=WorkloadPlacement(runtime="host"),
                )
            )
    finally:
        rt.stop()


def test_host_enabled_via_start_options() -> None:
    import sys

    rt = EmbeddedRuntime()
    rt.start(
        storage_backend="memory",
        workload_host_enabled=True,
    )
    try:
        wl = rt.workload.start(
            WorkloadSpec(
                kind=WorkloadKind.RUN,
                isolation=IsolationPolicy.BEST_EFFORT,
                lifecycle=LifecyclePolicy.JOB,
                command=(sys.executable, "-c", "print('wired')"),
                placement=WorkloadPlacement(runtime="host"),
            )
        )
        assert wl.result is not None and wl.result.success
    finally:
        rt.stop()


def test_doctor_includes_workloads_and_host_warning() -> None:
    import plugins.runners  # noqa: F401

    rt = EmbeddedRuntime()
    rt.start(
        storage_backend="memory",
        workload_host_enabled=True,
    )
    try:
        report = build_doctor_report(rt)
        assert "workloads" in report
        assert report["workloads"].get("engine_initialized") is True
        assert "host" in report["registries"].get("workload_runtimes", [])
        assert any("host" in i.lower() and "enabled" in i.lower() for i in report["issues"])
    finally:
        rt.stop()
