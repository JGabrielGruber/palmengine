"""Tests for ProcessExecutionService."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.core.orchestration import JobStatus


@pytest.fixture
def host(fast_settings: PalmSettings) -> Iterator[ApplicationHost]:
    application_host = ApplicationHost(
        settings=fast_settings,
        profile=HostProfile.all_in_one(),
    )
    application_host.start()
    yield application_host
    application_host.shutdown()


def test_process_execution_run_returns_jobs(host: ApplicationHost) -> None:
    result = host.execution.processes.run(
        "pipeline",
        body={
            "process": {
                "name": "pipeline",
                "flows": [
                    {"name": "extract", "pattern": "etl"},
                    {"name": "graph", "pattern": "dag"},
                ],
            }
        },
    )
    assert "jobs" in result
    assert len(result["jobs"]) == 2
    assert result["jobs"][0]["status"] == JobStatus.SUCCEEDED.value


def test_process_dispatch_run_path(host: ApplicationHost) -> None:
    result = host.execution.processes.dispatch(
        ["processes", "pipeline", "run"],
        {
            "body": {
                "process": {
                    "name": "pipeline",
                    "flows": [{"name": "extract", "pattern": "etl"}],
                }
            }
        },
    )
    assert "jobs" in result