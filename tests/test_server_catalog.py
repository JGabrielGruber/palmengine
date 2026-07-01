"""Tests for REST catalog and snapshot endpoints."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition, ProcessDefinition, ResourceDefinition
from palm.instances import ProcessInstance, StateSnapshot
from palm.runtimes.server import ServerRuntime


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    yield rt
    rt.stop()


def _request(
    base_url: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | str]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            if "application/json" in resp.headers.get("Content-Type", ""):
                return resp.status, json.loads(raw)
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        if "application/json" in exc.headers.get("Content-Type", ""):
            return exc.code, json.loads(raw)
        return exc.code, raw


def _sample_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-api-1",
        name="api-flow",
        pattern="wizard",
        options={"steps": [{"slug": "one", "title": "One", "prompt": "One?"}]},
    )


def _sample_process() -> ProcessDefinition:
    return ProcessDefinition(
        id="proc-api-1",
        name="api-process",
        flows=[_sample_flow()],
        metadata={"source": "test"},
    )


def _seed_instance(server: ServerRuntime, *, instance_id: str = "inst-api") -> None:
    flow = _sample_flow()
    inst = ProcessInstance(
        instance_id=instance_id,
        job_id="job-api",
        status=JobStatus.WAITING_FOR_INPUT.value,
        state_snapshot={"k": 1},
        flow_definition=flow.to_dict(),
        pattern="wizard",
    )
    inst.append_state_snapshot(
        StateSnapshot(
            status="WAITING_FOR_INPUT",
            recorded_at="2026-06-17T12:00:00+00:00",
            state_snapshot={"k": 1},
            job_id="job-api",
        )
    )
    inst.append_state_snapshot(
        StateSnapshot(
            status="SUCCEEDED",
            recorded_at="2026-06-17T12:05:00+00:00",
            state_snapshot={"k": 2},
            job_id="job-api",
        )
    )
    server.instance_manager.save(inst)


def test_list_and_get_flows(server: ServerRuntime) -> None:
    server.repository.register_flow(_sample_flow())

    status, payload = _request(server.base_url, "GET", "/v1/api/definitions/flows")
    assert status == 200
    assert isinstance(payload, dict)
    assert len(payload["flows"]) == 1
    assert payload["flows"][0]["flow_id"] == "flow-api-1"
    assert payload["flows"][0]["pattern"] == "wizard"
    assert payload["flows"][0]["step_slugs"] == ["one"]
    assert "pagination" in payload

    status, payload = _request(server.base_url, "GET", "/v1/api/definitions/flows/flow-api-1")
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["name"] == "api-flow"
    assert payload["pattern"] == "wizard"

    status, slim = _request(server.base_url, "GET", "/v1/api/definitions/flows/flow-api-1?verbose=0")
    assert status == 200
    assert isinstance(slim, dict)
    assert slim["step_slugs"] == ["one"]
    assert "options" not in slim

    status, payload = _request(server.base_url, "GET", "/v1/api/definitions/flows/missing")
    assert status == 404
    assert isinstance(payload, dict)
    assert payload["error"] == "flow_not_found"


def test_list_flows_filters_by_pattern(server: ServerRuntime) -> None:
    server.repository.register_flow(_sample_flow())
    server.repository.register_flow(FlowDefinition(name="dag-flow", pattern="dag", options={}))

    status, payload = _request(server.base_url, "GET", "/v1/api/definitions/flows?pattern=wizard")
    assert status == 200
    assert isinstance(payload, dict)
    assert len(payload["flows"]) == 1
    assert payload["flows"][0]["pattern"] == "wizard"


def test_list_and_get_processes(server: ServerRuntime) -> None:
    server.repository.register_process(_sample_process())

    status, payload = _request(server.base_url, "GET", "/v1/api/definitions/processes")
    assert status == 200
    assert isinstance(payload, dict)
    assert len(payload["processes"]) == 1
    assert payload["processes"][0]["process_id"] == "proc-api-1"
    assert payload["processes"][0]["flow_count"] == 1

    status, payload = _request(server.base_url, "GET", "/v1/api/definitions/processes/proc-api-1")
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["name"] == "api-process"
    assert len(payload["flows"]) == 1

    status, payload = _request(server.base_url, "GET", "/v1/api/definitions/processes/missing")
    assert status == 404
    assert isinstance(payload, dict)
    assert payload["error"] == "process_not_found"


def test_list_and_get_snapshots(server: ServerRuntime) -> None:
    _seed_instance(server)

    status, payload = _request(server.base_url, "GET", "/v1/api/system/instances/inst-api/snapshots")
    assert status == 200
    assert isinstance(payload, dict)
    assert len(payload["snapshots"]) == 2
    assert payload["snapshots"][0]["snapshot_id"] == "0"
    assert payload["snapshots"][1]["snapshot_id"] == "1"
    assert payload["snapshots"][0]["recorded_at"] == "2026-06-17T12:00:00+00:00"

    status, payload = _request(server.base_url, "GET", "/v1/api/system/instances/inst-api/snapshots/1")
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["snapshot_id"] == "1"
    assert payload["status"] == "SUCCEEDED"
    assert payload["state_snapshot"]["k"] == 2

    status, payload = _request(
        server.base_url,
        "GET",
        "/v1/api/system/instances/inst-api/snapshots/2026-06-17T12:00:00+00:00",
    )
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["snapshot_id"] == "0"

    status, payload = _request(server.base_url, "GET", "/v1/api/system/instances/inst-api/snapshots/missing")
    assert status == 404
    assert isinstance(payload, dict)
    assert payload["error"] == "snapshot_not_found"

    status, payload = _request(server.base_url, "GET", "/v1/api/system/instances/unknown/snapshots")
    assert status == 404
    assert isinstance(payload, dict)
    assert payload["error"] == "instance_not_found"


def test_list_and_get_resources(server: ServerRuntime) -> None:
    import palm.providers  # noqa: F401 — register providers

    server.repository.register_resource(
        ResourceDefinition(
            id="resource-api-1",
            name="api-resource",
            provider="rest",
            action="fetch",
            resource_id="items/{id}",
            params={"id": "{{ state.id }}"},
        )
    )

    status, payload = _request(server.base_url, "GET", "/v1/api/definitions/resources")
    assert status == 200
    assert isinstance(payload, dict)
    assert len(payload["resources"]) == 1
    assert payload["resources"][0]["name"] == "api-resource"
    assert payload["resources"][0]["provider"] == "rest"

    status, payload = _request(server.base_url, "GET", "/v1/api/definitions/resources/api-resource")
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["name"] == "api-resource"
    assert "param_keys" in payload

    status, payload = _request(server.base_url, "GET", "/v1/api/definitions/resources/missing")
    assert status == 404
    assert isinstance(payload, dict)
    assert payload["error"] == "resource_not_found"


def test_openapi_and_docs_include_catalog_and_snapshots(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/v1/openapi.json")
    assert status == 200
    assert isinstance(payload, dict)
    tag_names = {tag["name"] for tag in payload["tags"]}
    assert "Plans" in tag_names
    assert "/v1/plans/prepare" in payload["paths"]

    status, payload = _request(server.base_url, "GET", "/v1/docs")
    assert status == 200
    assert isinstance(payload, str)
    assert "Plans" in payload
    assert "/v1/plans/prepare" in payload
