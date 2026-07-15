"""Tests for Palm Studio SSR surface."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.definitions import FlowDefinition
from palm.runtimes.server import ServerRuntime
from palm.runtimes.server.surfaces.ssr.studio.api.drafts import clear_drafts


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    yield rt
    rt.stop()


def _get(base_url: str, path: str) -> tuple[int, str, dict[str, str]]:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Accept": "text/html,application/json,*/*"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        headers = {key.lower(): value for key, value in resp.headers.items()}
        return resp.status, resp.read().decode("utf-8", errors="replace"), headers


def test_studio_index_renders(server: ServerRuntime) -> None:
    status, html, headers = _get(server.base_url, "/studio")
    assert status == 200
    assert "text/html" in headers.get("content-type", "")
    assert "Palm Studio" in html
    assert "__PALM_STUDIO__" in html


def test_studio_surface_info(server: ServerRuntime) -> None:
    req = urllib.request.Request(
        f"{server.base_url}/v1/surfaces/studio",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    assert payload["status"] == "active"
    assert payload["home"] == "/studio"
    assert payload["surface"] == "studio"


def _json(
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
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_studio_palette_lists_registry_sections(server: ServerRuntime) -> None:
    server.repository.register_flow(
        FlowDefinition(
            id="studio-template-flow",
            name="studio-template",
            pattern="wizard",
            options={"steps": []},
        )
    )
    status, payload = _json(server.base_url, "GET", "/v1/studio/palette")
    assert status == 200
    section_ids = {section["id"] for section in payload["sections"]}
    assert section_ids == {"structural", "patterns", "transforms", "resources", "flows"}
    patterns = next(s for s in payload["sections"] if s["id"] == "patterns")
    assert any(item["kind"] == "pattern" for item in patterns["items"])
    transforms = next(s for s in payload["sections"] if s["id"] == "transforms")
    assert any(item["ref"] == "rename_field" for item in transforms["items"])
    flows = next(s for s in payload["sections"] if s["id"] == "flows")
    assert any(item["ref"] == "studio-template-flow" for item in flows["items"])


def test_studio_draft_save_and_load(server: ServerRuntime) -> None:
    clear_drafts()
    body = {
        "name": "demo-flow",
        "pattern": "wizard",
        "canvas": {"nodes": [{"id": "n1"}], "edges": []},
    }
    status, created = _json(server.base_url, "POST", "/v1/studio/drafts", body=body)
    assert status == 200
    draft_id = created["draft"]["id"]
    assert created["draft"]["name"] == "demo-flow"

    status, loaded = _json(server.base_url, "GET", f"/v1/studio/drafts/{draft_id}")
    assert status == 200
    assert loaded["draft"]["canvas"]["nodes"][0]["id"] == "n1"

    status, listing = _json(server.base_url, "GET", "/v1/studio/drafts")
    assert status == 200
    assert any(row["id"] == draft_id for row in listing["drafts"])


def test_studio_extensions_contract(server: ServerRuntime) -> None:
    status, payload = _json(server.base_url, "GET", "/v1/studio/extensions")
    assert status == 200
    assert "canvas:node:added" in payload["events"]
    assert "plugin:registered" in payload["events"]
    assert "action" in payload["node_type_kinds"]
    assert "register" in payload["plugin_contract"]["register"]


def test_studio_save_flow_registers_in_repository(server: ServerRuntime) -> None:
    body = {
        "version": 1,
        "kind": "flow",
        "id": "studio-saved-flow",
        "name": "studio-saved-flow",
        "pattern": "wizard",
        "options": {
            "steps": [{"slug": "one", "title": "One", "prompt": "One?"}],
        },
    }
    status, payload = _json(server.base_url, "POST", "/v1/studio/definitions/flows", body=body)
    assert status == 200
    assert payload["saved"] is True
    assert payload["flow"]["name"] == "studio-saved-flow"

    status, listed = _json(server.base_url, "GET", "/v1/api/definitions/flows")
    assert status == 200
    assert any(row["flow_id"] == "studio-saved-flow" for row in listed["flows"])


def test_studio_save_process_registers_in_repository(server: ServerRuntime) -> None:
    body = {
        "version": 1,
        "kind": "process",
        "id": "studio-saved-process",
        "name": "studio-saved-process",
        "storage": "memory",
        "metadata": {"source": "studio"},
        "flows": [
            {
                "version": 1,
                "kind": "flow",
                "id": "nested-flow",
                "name": "nested-flow",
                "pattern": "wizard",
                "options": {"steps": []},
            }
        ],
    }
    status, payload = _json(server.base_url, "POST", "/v1/studio/definitions/processes", body=body)
    assert status == 200
    assert payload["saved"] is True
    assert payload["process"]["name"] == "studio-saved-process"

    status, listed = _json(server.base_url, "GET", "/v1/api/definitions/processes")
    assert status == 200
    assert any(row["process_id"] == "studio-saved-process" for row in listed["processes"])


def test_studio_templates_list_and_load(server: ServerRuntime) -> None:
    status, payload = _json(server.base_url, "GET", "/v1/studio/templates")
    assert status == 200
    assert len(payload["templates"]) >= 2
    assert "getting-started" in payload["categories"]

    template_id = payload["templates"][0]["id"]
    status, detail = _json(server.base_url, "GET", f"/v1/studio/templates/{template_id}")
    assert status == 200
    assert detail["template"]["flow"]["pattern"]

    encoded_id = "template%3Apipeline-transform"
    status, encoded = _json(server.base_url, "GET", f"/v1/studio/templates/{encoded_id}")
    assert status == 200
    assert encoded["template"]["id"] == "template:pipeline-transform"


def test_health_reports_studio(server: ServerRuntime) -> None:
    req = urllib.request.Request(
        f"{server.base_url}/health",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    assert "studio" in payload["surfaces"]
    assert payload["studio"] == "/studio"
