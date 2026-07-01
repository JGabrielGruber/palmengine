"""Tests for GET /v1/instances/{instance_id}/tree."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition, ResourceDefinition
from palm.runtimes.server import ServerRuntime


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
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            if "application/json" in resp.headers.get("Content-Type", ""):
                return resp.status, json.loads(raw)
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        if "application/json" in exc.headers.get("Content-Type", ""):
            return exc.code, json.loads(raw)
        return exc.code, raw


def _child_wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-child-wizard",
        name="child-wizard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "question", "title": "Question", "prompt": "Child question?"},
            ],
        },
    )


def _parent_wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-parent-wizard",
        name="parent-wizard",
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "spawn_child",
                    "title": "Spawn Child Wizard",
                    "step_kind": "resource",
                    "resource_ref": "submit-child-wizard",
                    "output_key": "child_job",
                },
            ],
        },
    )


def _submit_child_resource() -> ResourceDefinition:
    return ResourceDefinition(
        id="resource-submit-child-wizard",
        name="submit-child-wizard",
        provider="palm",
        action="submit_flow",
        resource_id="flow:child-wizard",
        params={
            "wait": True,
            "wait_mode": "until_input",
            "timeout_seconds": 5,
        },
    )


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    rt.repository.save_flow(_child_wizard_flow())
    rt.repository.save_flow(_parent_wizard_flow())
    rt.repository.save_resource(_submit_child_resource())
    yield rt
    rt.stop()


def test_get_instance_tree_reports_nested_child(server: ServerRuntime) -> None:
    status, created = _request(
        server.base_url,
        "POST",
        "/v1/api/flows/parent-wizard/create",
        body={"flow_name": "parent-wizard"},
    )
    assert status in {200, 202}
    assert isinstance(created, dict)
    parent_job_id = created["job_id"]

    status, parent_ctx = _request(
        server.base_url,
        "GET",
        f"/v1/api/system/jobs/{parent_job_id}/context",
    )
    assert status == 200
    assert isinstance(parent_ctx, dict)
    parent_instance_id = str(parent_ctx["instance"]["instance_id"])

    status, tree = _request(
        server.base_url,
        "GET",
        f"/v1/api/system/instances/{parent_instance_id}/tree",
    )
    assert status == 200
    assert isinstance(tree, dict)
    assert tree["root"]["flow"] == "parent-wizard"
    assert tree["active_child"] is not None
    assert tree["active_child"]["status"] == JobStatus.WAITING_FOR_INPUT.value
    assert "explorer" in tree["links"]
