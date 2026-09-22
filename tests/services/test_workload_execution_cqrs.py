"""WorkloadExecutionService + CQRS (0.56 product path)."""

from __future__ import annotations

import sys
from collections.abc import Iterator

import pytest

from bundles.standard.app import ApplicationHost, DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.common.cqrs.schemas import build_schema_registry
from palm.core.workload import WorkloadPolicyError
from palm.services.execution.workloads.bindings.cqrs.commands import (
    ExecWorkloadCommand,
    StartWorkloadCommand,
    StopWorkloadCommand,
)
from palm.services.execution.workloads.bindings.cqrs.queries import (
    GetWorkloadQuery,
    ListWorkloadHostsQuery,
    ListWorkloadRuntimesQuery,
    ListWorkloadsQuery,
)


@pytest.fixture
def host() -> Iterator[ApplicationHost]:
    settings = PalmSettings.for_tests(load_examples=False)
    settings.workload_host_enabled = True
    h = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    h.start()
    yield h
    h.shutdown()


def test_workload_cqrs_schemas_registered() -> None:
    # Ensure contributor import side-effect
    import palm.services.execution.workloads  # noqa: F401

    registry = build_schema_registry()
    assert StartWorkloadCommand in registry.command_types()
    assert GetWorkloadQuery in registry.query_types()
    assert ListWorkloadRuntimesQuery in registry.query_types()


def test_start_run_via_service(host: ApplicationHost) -> None:
    svc = host.execution.workloads
    wl = svc.start(
        {
            "kind": "run",
            "isolation": "best_effort",
            "lifecycle": "job",
            "command": [sys.executable, "-c", "print('svc-ok')"],
            "placement": {"runtime": "host"},
        },
        owner={"job_id": "j-svc"},
    )
    assert wl["status"] == "STOPPED"
    assert wl["result"]["exit_code"] == 0
    assert "svc-ok" in wl["result"]["stdout_tail"]


def test_start_via_command_bus(host: ApplicationHost) -> None:
    wl = host.execute(
        StartWorkloadCommand(
            spec={
                "kind": "run",
                "isolation": "best_effort",
                "lifecycle": "job",
                "command": [sys.executable, "-c", "print('bus')"],
                "placement": {"runtime": "host"},
            },
            owner={"job_id": "j-bus"},
        )
    )
    assert wl["status"] == "STOPPED"
    got = host.ask(GetWorkloadQuery(workload_id=wl["workload_id"]))
    assert got["workload_id"] == wl["workload_id"]


def test_workspace_start_exec_stop_via_cqrs(host: ApplicationHost) -> None:
    started = host.execute(
        StartWorkloadCommand(
            spec={
                "kind": "workspace",
                "isolation": "host",
                "lifecycle": "session",
                "placement": {"runtime": "host"},
            },
            owner={"session_id": "sess-ws"},
        )
    )
    assert started["status"] == "READY"
    assert started["handle"]["connection_hints"]["workdir"]

    result = host.execute(
        ExecWorkloadCommand(
            workload_id=started["workload_id"],
            command=[sys.executable, "-c", "print('warm-exec')"],
        )
    )
    assert result["exit_code"] == 0
    assert "warm-exec" in result["stdout_tail"]

    # Workspace remains READY after successful exec
    still = host.ask(GetWorkloadQuery(workload_id=started["workload_id"]))
    assert still["status"] == "READY"

    stopped = host.execute(StopWorkloadCommand(workload_id=started["workload_id"]))
    assert stopped["status"] == "STOPPED"


def test_list_hosts_and_runtimes(host: ApplicationHost) -> None:
    hosts = host.ask(ListWorkloadHostsQuery())
    assert any(h["id"] == "local" for h in hosts)
    runtimes = host.ask(ListWorkloadRuntimesQuery())
    names = {r["name"] for r in runtimes}
    assert "host" in names
    assert "neonroot" in names


def test_list_workloads_filter(host: ApplicationHost) -> None:
    host.execute(
        StartWorkloadCommand(
            spec={
                "kind": "workspace",
                "isolation": "best_effort",
                "lifecycle": "session",
                "placement": {"runtime": "host"},
            },
            owner={"session_id": "s-list"},
        )
    )
    rows = host.ask(ListWorkloadsQuery(session_id="s-list"))
    assert len(rows) == 1


def test_host_disabled_without_flag() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    assert settings.workload_host_enabled is False
    h = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    h.start()
    try:
        with pytest.raises(WorkloadPolicyError, match="disabled"):
            h.execution.workloads.start(
                {
                    "kind": "run",
                    "isolation": "host",
                    "lifecycle": "job",
                    "command": ["true"],
                    "placement": {"runtime": "host"},
                }
            )
    finally:
        h.shutdown()
