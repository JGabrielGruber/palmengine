"""0.35.6 — static /analytics dogfood UI."""

from __future__ import annotations

import urllib.request

import pytest

from palm.runtimes.server import ServerRuntime


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    yield rt
    rt.stop()


def _get(url: str) -> tuple[int, str, str]:
    req = urllib.request.Request(url, headers={"Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, resp.headers.get("Content-Type", ""), resp.read().decode(
            "utf-8", errors="replace"
        )


def test_analytics_index_and_assets(server: ServerRuntime) -> None:
    status, ctype, body = _get(f"{server.base_url}/analytics/")
    assert status == 200
    assert "text/html" in ctype
    assert "Palm Analytics" in body
    assert "analytics.js" in body

    status, ctype, js = _get(f"{server.base_url}/analytics/analytics.js")
    assert status == 200
    assert "javascript" in ctype or "text/" in ctype
    assert "v1/api/analytics" in js

    status, ctype, css = _get(f"{server.base_url}/analytics/analytics.css")
    assert status == 200
    assert "css" in ctype

    # traversal blocked → 404
    try:
        urllib.request.urlopen(f"{server.base_url}/analytics/../secrets", timeout=5)
        raise AssertionError("expected 404")
    except Exception as exc:  # noqa: BLE001
        assert "404" in str(exc) or getattr(exc, "code", None) == 404
