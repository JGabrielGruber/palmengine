"""REST list jobs enrichment — instance_id must not mirror job_id."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.core.orchestration import JobStatus
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
) -> tuple[int, dict[str, Any]]:
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
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload


def test_list_waiting_jobs_resolves_instance_id(server: ServerRuntime) -> None:
    status, submit = _request(
        server.base_url,
        "POST",
        "/v1/wizards",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status == 202
    job_id = submit["job_id"]
    instance_id = submit["instance_id"]
    assert instance_id != job_id

    server.wait_until_idle()

    status, payload = _request(
        server.base_url,
        "GET",
        "/v1/jobs?status=WAITING_FOR_INPUT&limit=10",
    )
    assert status == 200
    rows = [row for row in payload["jobs"] if row.get("job_id") == job_id]
    assert len(rows) == 1
    row = rows[0]
    assert row["instance_id"] == instance_id
    assert row["status"] == JobStatus.WAITING_FOR_INPUT.value
    assert row.get("pattern") == "wizard"
    assert row.get("flow") == "onboard"