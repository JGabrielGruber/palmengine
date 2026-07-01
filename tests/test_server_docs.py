"""Tests for REST documentation generation and example accuracy."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

import pytest

from palm.runtimes.server import ServerRuntime
from palm.runtimes.server.surfaces.rest.doc_examples import (
    DEFAULT_BASE_URL,
    build_curl,
    featured_curl_examples,
    resolve_path,
    response_example,
)
from palm.runtimes.server.surfaces.rest.docs import build_docs_html
from palm.runtimes.server.surfaces.rest.route_table import rest_routes


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    yield rt
    rt.stop()


def _get_html(base_url: str, path: str) -> tuple[int, str]:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Accept": "text/html"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def test_build_docs_html_includes_rich_structure() -> None:
    from palm import __version__

    html = build_docs_html(version=__version__)
    assert "endpoint-card" in html
    assert "REST API Reference" in html
    assert 'href="/v1/openapi.json"' in html
    assert 'id="plans"' in html
    assert 'id="meta"' in html
    assert "copyExample" in html
    assert "Sample response" in html
    assert "Try it" in html


def test_every_route_has_curl_and_response_example() -> None:
    for route in rest_routes():
        curl = build_curl(route)
        assert route.method in curl
        assert resolve_path(route.path) in curl
        assert DEFAULT_BASE_URL in curl
        if route.request_schema:
            assert "-d '" in curl
        if route.auth_required:
            assert "X-Palm-Subject" in curl
        response = response_example(route)
        assert response, f"missing response example for {route.route_id}"


def test_curl_paths_use_resolved_parameters() -> None:
    routes_by_id = {route.route_id: route for route in rest_routes()}
    curl = build_curl(routes_by_id["prepare_plans"])
    assert "/v1/plans/prepare" in curl
    curl = build_curl(routes_by_id["health"])
    assert "/health" in curl


def test_featured_examples_cover_key_endpoints() -> None:
    titles = {item[0] for item in featured_curl_examples()}
    assert "Health check" in titles
    assert "List snapshots" in titles
    assert "List instances" in titles


def test_docs_endpoint_serves_rich_html(server: ServerRuntime) -> None:
    status, html = _get_html(server.base_url, "/v1/docs")
    assert status == 200
    assert "endpoint-card" in html
    assert "/v1/plans/prepare" in html
    assert "/health" in html
    assert "OpenAPI JSON" in html


def test_health_curl_example_matches_live_response(server: ServerRuntime) -> None:
    health_route = next(route for route in rest_routes() if route.route_id == "health")
    curl = build_curl(health_route, base_url=server.base_url)
    match = re.search(r"curl -s -X \w+ '([^']+)'", curl)
    assert match is not None
    url = match.group(1)

    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    assert payload["status"] == "ok"
    assert payload["docs"] == "/v1/docs"
    assert payload["openapi"] == "/v1/openapi.json"
