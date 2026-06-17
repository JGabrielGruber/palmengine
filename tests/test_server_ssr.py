"""Tests for SSR wiki surface and dynamic documentation hub."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.common.runtimes.server.ssr.fetch import SsrFetcher
from palm.common.runtimes.server.ssr.layout import wiki_page
from palm.definitions import FlowDefinition, ProcessDefinition
from palm.runtimes.server import ServerRuntime


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    yield rt
    rt.stop()


def _get_html(base_url: str, path: str) -> tuple[int, str, dict[str, str]]:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Accept": "text/html"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            headers = {key.lower(): value for key, value in resp.headers.items()}
            return resp.status, resp.read().decode("utf-8"), headers
    except urllib.error.HTTPError as exc:
        headers = {key.lower(): value for key, value in exc.headers.items()}
        return exc.code, exc.read().decode("utf-8"), headers


def _post_json(base_url: str, path: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def test_wiki_overview_renders(server: ServerRuntime) -> None:
    status, html, _ = _get_html(server.base_url, "/wiki")
    assert status == 200
    assert "Palm Wiki" in html
    assert "Documentation Hub" in html
    assert "/wiki/flows" in html
    assert "/wiki/jobs" in html


def test_docs_redirects_to_wiki(server: ServerRuntime) -> None:
    import http.client
    from urllib.parse import urlparse

    parsed = urlparse(server.base_url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    conn.request("GET", "/docs", headers={"Accept": "text/html"})
    response = conn.getresponse()
    assert response.status == 302
    assert response.getheader("Location") == "/wiki"
    conn.close()


def test_ssr_surface_info_is_active(server: ServerRuntime) -> None:
    req = urllib.request.Request(
        f"{server.base_url}/v1/surfaces/ssr",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    assert payload["status"] == "active"
    assert payload["wiki"] == "/wiki"


def test_flow_catalog_page(server: ServerRuntime) -> None:
    server.repository.register_flow(
        FlowDefinition(
            id="wiki-flow-1",
            name="wiki-flow",
            pattern="wizard",
            options={"steps": [{"slug": "one", "title": "One", "prompt": "One?"}]},
        )
    )
    status, html, _ = _get_html(server.base_url, "/wiki/flows")
    assert status == 200
    assert "wiki-flow" in html

    status, html, _ = _get_html(server.base_url, "/wiki/flows/wiki-flow-1")
    assert status == 200
    assert "wizard" in html


def test_process_and_pattern_pages(server: ServerRuntime) -> None:
    flow = FlowDefinition(name="p-flow", pattern="wizard", options={})
    server.repository.register_process(
        ProcessDefinition(id="wiki-proc", name="wiki-proc", flows=[flow])
    )

    status, html, _ = _get_html(server.base_url, "/wiki/processes")
    assert status == 200
    assert "wiki-proc" in html

    status, html, _ = _get_html(server.base_url, "/wiki/patterns")
    assert status == 200
    assert "wizard" in html


def test_job_context_viewer(server: ServerRuntime) -> None:
    _, payload = _post_json(
        server.base_url,
        "/v1/jobs",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    job_id = payload["job_id"]

    status, html, _ = _get_html(server.base_url, f"/wiki/jobs/{job_id}")
    assert status == 200
    assert job_id in html
    assert "Next actions" in html
    assert "provide_input" in html
    assert "/v1/jobs/" in html


def test_health_includes_wiki_link(server: ServerRuntime) -> None:
    req = urllib.request.Request(f"{server.base_url}/health", method="GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    assert payload["wiki"] == "/wiki"


def test_ssr_fetcher_lists_patterns(server: ServerRuntime) -> None:
    app = server.server_app
    assert app is not None
    fetcher = SsrFetcher(app.context)
    patterns = fetcher.list_patterns()
    assert any(item["name"] == "wizard" for item in patterns)


def test_wiki_layout_renders_title() -> None:
    html = wiki_page(title="Test", version="0.10.9", content="<p>Body</p>")
    assert "Test" in html
    assert "Body" in html