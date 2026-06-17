"""Tests for REST surface structure, schema validation, and documentation."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.core.context.state_schema import DictStateSchema
from palm.runtimes.server import ServerRuntime
from palm.runtimes.server.surfaces.rest.route_table import rest_routes
from palm.runtimes.server.surfaces.rest.schema_validation import schema_errors_to_details
from palm.runtimes.server.surfaces.rest.schemas import SUBMIT_PLANS_BODY, submit_job_variant_errors


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


def test_rest_routes_are_grouped() -> None:
    groups = {route.group for route in rest_routes()}
    assert groups == {"Meta", "Jobs", "Plans", "Instances"}


def test_submit_job_requires_flow_variant() -> None:
    errors = submit_job_variant_errors({})
    assert errors
    details = schema_errors_to_details(errors)
    assert details[0]["field"] == "body"


def test_dict_state_schema_plan_ids_validation() -> None:
    errors = SUBMIT_PLANS_BODY.validate_state({})
    assert any("plan_ids" in message for message in errors)


def test_openapi_includes_tags_and_examples(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/v1/openapi.json")
    assert status == 200
    assert isinstance(payload, dict)
    tag_names = {tag["name"] for tag in payload["tags"]}
    assert "Jobs" in tag_names
    submit_op = payload["paths"]["/v1/jobs"]["post"]
    assert "requestBody" in submit_op
    assert "examples" in submit_op["requestBody"]["content"]["application/json"]


def test_docs_endpoint_returns_html(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/v1/docs")
    assert status == 200
    assert isinstance(payload, str)
    assert "Palm Engine API" in payload
    assert "/v1/openapi.json" in payload


def test_health_includes_doc_links(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/health")
    assert status == 200
    assert isinstance(payload, dict)
    assert payload["docs"] == "/v1/docs"
    assert payload["openapi"] == "/v1/openapi.json"


def test_submit_job_validation_error(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "POST", "/v1/jobs", body={})
    assert status == 400
    assert isinstance(payload, dict)
    assert payload["error"] in {"validation_failed", "invalid_request"}
    assert "details" in payload


def test_submit_plans_schema_validation(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/plans/submit",
        body={"plan_ids": []},
    )
    assert status == 400
    assert isinstance(payload, dict)
    assert payload["error"] == "validation_failed"
    assert payload["details"][0]["field"] == "plan_ids"