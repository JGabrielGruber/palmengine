"""Tests for ServerRuntime deferred plan HTTP API and auth."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.core.orchestration import JobStatus
from palm.runtimes.server import PALM_SUBJECT_HEADER, ServerRuntime


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0, auth_enforce=True)
    yield rt
    rt.stop()


def _request(
    base_url: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    subject: str | None = "ada",
) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {"Accept": "application/json"}
    if subject is not None:
        headers[PALM_SUBJECT_HEADER] = subject
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
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload


def test_http_requires_auth_when_enforced(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/jobs",
        body={"wizard": {"steps": 1}},
        subject=None,
    )
    assert status == 401
    assert payload["error"] == "unauthorized"


def test_prepare_and_submit_plans_http(server: ServerRuntime) -> None:
    status, prepared = _request(
        server.base_url,
        "POST",
        "/v1/plans/prepare",
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
    assert status == 201
    assert len(prepared["plans"]) == 2
    plan_ids = [item["plan_id"] for item in prepared["plans"]]

    status, submitted = _request(
        server.base_url,
        "POST",
        "/v1/plans/submit",
        body={"plan_ids": plan_ids},
    )
    assert status == 202
    assert len(submitted["jobs"]) == 2
    assert submitted["jobs"][0]["status"] == JobStatus.SUCCEEDED.value
    assert submitted["jobs"][1]["status"] == JobStatus.SUCCEEDED.value


def test_submit_plans_rejects_unknown_plan_id(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/plans/submit",
        body={"plan_ids": ["plan-missing"]},
    )
    assert status == 404
    assert payload["error"] == "plan_not_found"