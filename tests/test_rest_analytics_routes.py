"""0.35.4b — REST /v1/api/analytics/*."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

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
    headers = {"Accept": "application/json", "X-Palm-Subject": "dev"}
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
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": raw}


def _err_code(body: dict[str, Any]) -> str:
    return str(body.get("error") or body.get("code") or "")


def test_list_datasets(server: ServerRuntime) -> None:
    status, body = _request(server.base_url, "GET", "/v1/api/analytics/datasets")
    assert status == 200
    assert isinstance(body.get("datasets"), list)


def test_describe_missing_404(server: ServerRuntime) -> None:
    status, body = _request(
        server.base_url, "GET", "/v1/api/analytics/datasets/no-such-dataset-xyz"
    )
    assert status == 404
    assert _err_code(body) == "dataset_not_found"


def test_query_published_kv_default(server: ServerRuntime) -> None:
    status, created = _request(
        server.base_url,
        "POST",
        "/v1/api/definitions/resources",
        body={
            "name": "analytics-rest-fact",
            "provider": "kv",
            "action": "get",
            "resource_id": "analytics/rest-fact",
            "params": {
                "namespace": "analytics",
                "backend": "memory",
                "default": {
                    "items": [
                        {"day": "d1", "revenue": 5},
                        {"day": "d2", "revenue": 7},
                    ]
                },
            },
            "metadata": {
                "analytics": {
                    "published": True,
                    "kind": "fact",
                    "row_path": "value.items",
                    "default_profile": "table",
                }
            },
        },
    )
    assert status == 201, created

    status, body = _request(
        server.base_url,
        "POST",
        "/v1/api/analytics/query",
        body={
            "dataset": "analytics-rest-fact",
            "profile": "table",
            "select": ["day", "revenue"],
        },
    )
    assert status == 200, body
    assert body.get("status") == "ok"
    assert body["data"]["columns"] == ["day", "revenue"]
    assert body["data"]["rows"] == [["d1", 5], ["d2", 7]]
