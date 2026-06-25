"""Tests for the built-in palm compositional provider."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from examples.definitions.data_ingestion import INGEST_ETL_FLOW
from palm.core.orchestration import JobStatus
from palm.definitions import ResourceDefinition
from palm.providers.palm.provider import PalmProvider
from palm.providers.palm.bindings.recursion.guard import (
    PalmRecursionError,
    RecursionLimits,
    palm_invoke_frame,
)
from palm.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.server import ServerRuntime


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    rt = EmbeddedRuntime()
    rt.start()
    rt.repository.save_flow(INGEST_ETL_FLOW)
    yield rt
    rt.stop()
    clear_palm_runtime()


def _palm_provider() -> PalmProvider:
    provider = PalmProvider(name="palm")
    provider.connect()
    return provider


def test_palm_provider_local_submit_flow_wait(runtime: EmbeddedRuntime) -> None:
    provider = _palm_provider()
    result = provider.invoke(
        "submit_flow",
        resource_id="flow:ingest-etl",
        params={"wait": True, "wait_timeout": 5},
    )
    assert result.success is True
    assert result.data["status"] == JobStatus.SUCCEEDED.value
    assert result.data["job_id"]
    assert result.metadata["mode"] == "local"
    assert result.data["invoke_depth"] == 1


def test_palm_provider_fire_and_forget(runtime: EmbeddedRuntime) -> None:
    provider = _palm_provider()
    result = provider.invoke(
        "submit_flow",
        params={"flow_name": "ingest-etl", "wait": False},
    )
    assert result.success is True
    assert result.data["job_id"]
    job = runtime.get_job(result.data["job_id"])
    assert job.status in {JobStatus.SUCCEEDED, JobStatus.RUNNING, JobStatus.PENDING}


def test_palm_provider_fetch_job(runtime: EmbeddedRuntime) -> None:
    job = runtime.submit_flow("ingest-etl")
    runtime.wait_until_idle()
    provider = _palm_provider()
    result = provider.invoke("fetch", resource_id=job.id)
    assert result.success is True
    assert result.data["job_id"] == job.id
    assert result.data["status"] == JobStatus.SUCCEEDED.value


def test_palm_provider_recursion_depth_limit(runtime: EmbeddedRuntime) -> None:
    provider = _palm_provider()
    with palm_invoke_frame("flow", "parent", limits=RecursionLimits(max_depth=1)):
        blocked = provider.invoke(
            "submit_flow",
            params={"flow_name": "ingest-etl", "max_depth": 1, "wait": False},
        )
    assert blocked.success is False
    assert "depth" in (blocked.error or "").lower()


def test_palm_provider_cycle_detection() -> None:
    with pytest.raises(PalmRecursionError):
        with palm_invoke_frame("flow", "cycle-a"):
            with palm_invoke_frame("flow", "cycle-b"):
                with palm_invoke_frame("flow", "cycle-a"):
                    pass


def test_palm_provider_invoke_resource(runtime: EmbeddedRuntime) -> None:
    runtime.repository.save_resource(
        ResourceDefinition(
            id="resource-rest-health",
            name="rest-health",
            provider="rest",
            action="fetch",
            resource_id="health/check",
        ),
    )
    provider = _palm_provider()
    result = provider.invoke(
        "invoke_resource",
        resource_id="resource:rest-health",
    )
    assert result.success is True
    assert result.data["kind"] == "resource"
    assert result.data["result"]["source"] == "rest"


def test_palm_provider_remote_submit_flow() -> None:
    server = ServerRuntime(host="127.0.0.1", port=0)
    server.start(port=0)
    server.repository.save_flow(INGEST_ETL_FLOW)
    try:
        provider = _palm_provider()
        result = provider.invoke(
            "submit_flow",
            params={
                "flow_name": "ingest-etl",
                "remote_url": server.base_url,
                "wait": True,
                "wait_timeout": 10,
            },
        )
        assert result.success is True
        assert result.metadata["mode"] == "remote"
        assert result.data["status"] == JobStatus.SUCCEEDED.value
    finally:
        server.stop()
        clear_palm_runtime()


def test_palm_provider_describe_and_health(runtime: EmbeddedRuntime) -> None:
    provider = _palm_provider()
    descriptor = provider.describe()
    assert descriptor.name == "palm"
    action_names = {item.name for item in descriptor.actions}
    assert action_names == {"submit_flow", "submit_process", "invoke_resource", "fetch"}
    assert provider.health().healthy is True
