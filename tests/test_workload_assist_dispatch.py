"""Assist/MCP path dispatch for workloads (0.56 small surface)."""

from __future__ import annotations

import sys

from bundles.standard.app import ApplicationHost, DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from bundles.standard.runtimes.mcp.assist.operator import dispatch_operator_path
from palm.services.assist.registry import list_mcp_path_aliases, resolve_mcp_alias


def test_workload_aliases_registered() -> None:
    aliases = {row["alias"] for row in list_mcp_path_aliases()}
    assert "workloads/start" in aliases
    assert "workloads/doctor" in aliases
    assert "workloads/runtimes" in aliases
    path = resolve_mcp_alias("workloads/stop", params={"workload_id": "w1"})
    assert list(path or ()) == ["workloads", "w1", "stop"]


def test_dispatch_workloads_start_and_doctor() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    host.start()
    try:

        class _Ctx:
            execution = host.execution

        doctor = dispatch_operator_path(_Ctx(), ["workloads", "doctor"], {})
        assert doctor["engine_initialized"] is True
        assert doctor["default_runtime"] == "local"

        started = dispatch_operator_path(
            _Ctx(),
            ["workloads", "start"],
            {
                "spec": {
                    "kind": "run",
                    "isolation": "best_effort",
                    "lifecycle": "job",
                    "command": [sys.executable, "-c", "print(7*6)"],
                    "placement": {"runtime": "local"},
                }
            },
        )
        assert started["status"] == "STOPPED"
        assert started["result"]["exit_code"] == 0
        assert "42" in (started["result"].get("stdout_tail") or "")

        runtimes = dispatch_operator_path(_Ctx(), ["workloads", "runtimes"], {})
        names = {r["name"] for r in runtimes["runtimes"]}
        assert "local" in names
    finally:
        host.shutdown()
