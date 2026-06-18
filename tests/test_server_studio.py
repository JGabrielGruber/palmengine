"""Tests for Palm Studio SSR surface."""

from __future__ import annotations

import json
import urllib.request

import pytest

from palm.runtimes.server import ServerRuntime


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