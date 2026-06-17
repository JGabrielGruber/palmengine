"""Tests for Palm Explorer surface and dynamic introspection hub."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import pytest

from palm.runtimes.server.surfaces.ssr.explorer.fetch import ExplorerFetcher
from palm.runtimes.server.surfaces.ssr.explorer.forms import flow_submit_form, schema_form
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page
from palm.runtimes.server.surfaces.ssr.explorer.pages.utils import (
    flow_description,
    flow_option_label,
    start_flow_href,
)
from palm.runtimes.server.surfaces.ssr.explorer.schemas import FLOW_SUBMIT_FORM, build_flow_submit_schema
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


@pytest.fixture
def sample_flow() -> FlowDefinition:
    return FlowDefinition(
        id="explorer-flow-1",
        name="explorer-flow",
        pattern="wizard",
        options={
            "description": "Demo onboarding wizard",
            "steps": [{"slug": "one", "title": "One", "prompt": "One?"}],
        },
    )


def test_explorer_overview_renders(server: ServerRuntime) -> None:
    status, html, _ = _get_html(server.base_url, "/explorer")
    assert status == 200
    assert "Palm Explorer" in html
    assert "Introspection Hub" in html
    assert "/explorer/flows" in html
    assert "/explorer/jobs" in html
    assert "/explorer/instances" in html


def test_docs_redirects_to_explorer(server: ServerRuntime) -> None:
    import http.client
    from urllib.parse import urlparse

    parsed = urlparse(server.base_url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    conn.request("GET", "/docs", headers={"Accept": "text/html"})
    response = conn.getresponse()
    assert response.status == 302
    assert response.getheader("Location") == "/explorer"
    conn.close()


def test_wiki_redirects_to_explorer(server: ServerRuntime) -> None:
    import http.client
    from urllib.parse import urlparse

    parsed = urlparse(server.base_url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    conn.request("GET", "/wiki", headers={"Accept": "text/html"})
    response = conn.getresponse()
    assert response.status == 302
    assert response.getheader("Location") == "/explorer"
    conn.close()


def test_explorer_surface_info_is_active(server: ServerRuntime) -> None:
    req = urllib.request.Request(
        f"{server.base_url}/v1/surfaces/explorer",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    assert payload["status"] == "active"
    assert payload["explorer"] == "/explorer"


def test_flow_catalog_page(server: ServerRuntime, sample_flow: FlowDefinition) -> None:
    server.repository.register_flow(sample_flow)
    status, html, _ = _get_html(server.base_url, "/explorer/flows")
    assert status == 200
    assert "explorer-flow" in html
    assert "Start" in html
    assert start_flow_href("explorer-flow-1") in html

    status, html, _ = _get_html(server.base_url, "/explorer/flows/explorer-flow-1")
    assert status == 200
    assert "wizard" in html
    assert "Start this flow" in html


def test_flow_submit_form_renders(server: ServerRuntime, sample_flow: FlowDefinition) -> None:
    server.repository.register_flow(sample_flow)
    status, html, _ = _get_html(server.base_url, "/explorer/flows/submit")
    assert status == 200
    assert 'name="flow_id"' in html
    assert 'name="submit_mode"' in html
    assert "explorer-flow · wizard" in html
    assert 'action="/explorer/flows/submit"' in html


def test_flow_submit_prefills_from_query(server: ServerRuntime, sample_flow: FlowDefinition) -> None:
    server.repository.register_flow(sample_flow)
    status, html, _ = _get_html(server.base_url, "/explorer/flows/submit?flow=explorer-flow-1")
    assert status == 200
    assert 'value="explorer-flow-1" selected' in html
    assert "Demo onboarding wizard" in html


def test_flow_submit_post_registered_flow(server: ServerRuntime, sample_flow: FlowDefinition) -> None:
    import http.client
    from urllib.parse import urlparse

    server.repository.register_flow(sample_flow)
    parsed = urlparse(server.base_url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    body = urllib.parse.urlencode(
        {
            "submit_mode": "registered",
            "flow_id": "explorer-flow-1",
        }
    ).encode("utf-8")
    conn.request(
        "POST",
        "/explorer/flows/submit",
        body=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response = conn.getresponse()
    assert response.status == 302
    location = response.getheader("Location", "")
    assert location.startswith("/explorer/jobs/")
    conn.close()


def test_process_and_pattern_pages(server: ServerRuntime) -> None:
    flow = FlowDefinition(name="p-flow", pattern="wizard", options={})
    server.repository.register_process(
        ProcessDefinition(id="explorer-proc", name="explorer-proc", flows=[flow])
    )

    status, html, _ = _get_html(server.base_url, "/explorer/processes")
    assert status == 200
    assert "explorer-proc" in html

    status, html, _ = _get_html(server.base_url, "/explorer/patterns")
    assert status == 200
    assert "wizard" in html


def test_job_context_viewer(server: ServerRuntime) -> None:
    _, payload = _post_json(
        server.base_url,
        "/v1/jobs",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    job_id = payload["job_id"]

    status, html, _ = _get_html(server.base_url, f"/explorer/jobs/{job_id}")
    assert status == 200
    assert job_id in html
    assert "Next actions" in html
    assert "provide_input" in html
    assert "Provide input" in html
    assert "/v1/jobs/" in html


def test_job_input_form_post(server: ServerRuntime) -> None:
    import http.client
    from urllib.parse import urlparse

    _, payload = _post_json(
        server.base_url,
        "/v1/jobs",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    job_id = payload["job_id"]

    parsed = urlparse(server.base_url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    body = urllib.parse.urlencode({"value": "Alice"}).encode("utf-8")
    conn.request(
        "POST",
        f"/explorer/jobs/{job_id}/input",
        body=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response = conn.getresponse()
    assert response.status == 302
    location = response.getheader("Location", "")
    assert location.startswith(f"/explorer/jobs/{job_id}")
    assert "notice=" in location or "error=" in location
    conn.close()


def test_instance_browser_page(server: ServerRuntime) -> None:
    _, payload = _post_json(
        server.base_url,
        "/v1/jobs",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    job_id = payload["job_id"]

    status, html, _ = _get_html(server.base_url, "/explorer/instances")
    assert status == 200
    assert "Instance Browser" in html
    assert job_id in html or "instance" in html.lower()


def test_health_includes_explorer_link(server: ServerRuntime) -> None:
    req = urllib.request.Request(f"{server.base_url}/health", method="GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    assert payload["explorer"] == "/explorer"
    assert payload["wiki"] == "/explorer"


def test_explorer_fetcher_lists_patterns(server: ServerRuntime) -> None:
    app = server.server_app
    assert app is not None
    fetcher = ExplorerFetcher(app.context)
    patterns = fetcher.list_patterns()
    assert any(item["name"] == "wizard" for item in patterns)


def test_explorer_layout_renders_title() -> None:
    html = explorer_page(title="Test", version="0.10.9", content="<p>Body</p>")
    assert "Test" in html
    assert "Body" in html
    assert "Palm Explorer" in html


def test_schema_form_renders_fields() -> None:
    html = schema_form(FLOW_SUBMIT_FORM, action="/explorer/flows/submit")
    assert 'name="submit_mode"' in html
    assert 'type="submit"' in html


def test_flow_submit_form_builder(sample_flow: FlowDefinition) -> None:
    html = flow_submit_form([sample_flow], selected_flow_id="explorer-flow-1")
    assert "explorer-flow · wizard · Demo onboarding wizard" in html
    assert 'value="explorer-flow-1" selected' in html
    assert "flow-context-panel" in html


def test_flow_utils(sample_flow: FlowDefinition) -> None:
    assert flow_description(sample_flow) == "Demo onboarding wizard"
    assert "explorer-flow" in flow_option_label(sample_flow)
    assert start_flow_href("my-flow") == "/explorer/flows/submit?flow=my-flow"


def test_build_flow_submit_schema(sample_flow: FlowDefinition) -> None:
    schema = build_flow_submit_schema([sample_flow])
    flow_spec = schema.definition["properties"]["flow_id"]
    assert "explorer-flow-1" in flow_spec["enum"]