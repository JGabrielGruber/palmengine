"""Explorer assist SSR — catalog, start, and assistant workspace."""

from __future__ import annotations

import http.client
import urllib.parse
import urllib.request
from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.runtimes.server import ServerRuntime


@pytest.fixture
def server() -> Iterator[ServerRuntime]:
    settings = PalmSettings.for_tests(load_examples=True)
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()
    rt = ServerRuntime(host="127.0.0.1", port=0, host_bridge=host)
    rt.start(port=0)
    yield rt
    rt.stop()
    host.shutdown()


def _get_html(base_url: str, path: str) -> tuple[int, str, dict[str, str]]:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Accept": "text/html"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        headers = {key.lower(): value for key, value in resp.headers.items()}
        return resp.status, resp.read().decode("utf-8"), headers


def _post_form(base_url: str, path: str) -> tuple[int, str, dict[str, str]]:
    parsed = urllib.parse.urlparse(base_url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=10)
    conn.request("POST", path, body=b"", headers={"Content-Type": "application/x-www-form-urlencoded"})
    response = conn.getresponse()
    headers = {key.lower(): value for key, value in response.getheaders()}
    raw = response.read().decode("utf-8")
    conn.close()
    return response.status, raw, headers


def test_explorer_assist_catalog(server: ServerRuntime) -> None:
    status, html, _ = _get_html(server.base_url, "/explorer/assist")
    assert status == 200
    assert "Assist" in html
    assert "operator-entry" in html
    assert "/explorer/assist/scenarios/operator-entry" in html


def test_explorer_assist_scenario_detail(server: ServerRuntime) -> None:
    status, html, _ = _get_html(server.base_url, "/explorer/assist/scenarios/operator-entry")
    assert status == 200
    assert "Start assist session" in html
    assert 'action="/explorer/assist/scenarios/operator-entry/start"' in html


def test_explorer_assist_start_redirects_to_session(server: ServerRuntime) -> None:
    status, _, headers = _post_form(
        server.base_url,
        "/explorer/assist/scenarios/operator-entry/start",
    )
    assert status == 302
    location = headers.get("location", "")
    assert "/explorer/assist/session/" in location

    session_path = urllib.parse.urlparse(location).path
    status, html, _ = _get_html(server.base_url, session_path)
    assert status == 200
    assert "assist-workspace" in html
    assert "What would you like to do with Palm?" in html
    assert "operator_hint" not in html


def test_explorer_nav_includes_assist(server: ServerRuntime) -> None:
    status, html, _ = _get_html(server.base_url, "/explorer")
    assert status == 200
    assert 'href="/explorer/assist"' in html