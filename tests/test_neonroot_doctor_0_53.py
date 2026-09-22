"""NeonRoot doctor (WorkloadRuntime, not provider)."""

from __future__ import annotations

from unittest.mock import patch

from plugins.runners.neonroot.cli import NeonrootProbe
from plugins.runners.neonroot.runtime import NeonrootWorkloadRuntime


def test_neonroot_doctor_section_available() -> None:
    import plugins.runners  # noqa: F401

    present = NeonrootProbe(available=True, path="/bin/neonroot", version="NeonRoot 0.0.2")
    with patch("plugins.runners.neonroot.cli.probe_neonroot", return_value=present):
        health = NeonrootWorkloadRuntime().health().to_dict()
    assert health["available"] is True
    assert "composition_declares" not in health


def test_neonroot_doctor_missing_cli_is_unavailable_not_declared() -> None:
    missing = NeonrootProbe(available=False, error="neonroot not found on PATH")
    with patch("plugins.runners.neonroot.cli.probe_neonroot", return_value=missing):
        health = NeonrootWorkloadRuntime().health().to_dict()
    assert health["available"] is False
    assert "composition_declares" not in health


def test_build_doctor_report_samples_neonroot_via_workloads() -> None:
    import plugins.runners  # noqa: F401
    from plugins.kits.server.diagnostics import build_doctor_report

    class _RT:
        runtime_name = "test"
        storage = None
        orchestration = None
        repository = None
        auth_enforce = False

    report = build_doctor_report(_RT())
    assert "neonroot" not in report
    assert "workload_host" not in report
    assert "neonroot" in report["workloads"]["registered_runtimes"]
