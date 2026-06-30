"""Tests for the REST provider HTTP bindings."""

from __future__ import annotations

import palm.providers  # noqa: F401
from palm.providers.rest.provider import RestProvider


def test_rest_provider_fetch_via_http(rest_base_url: str) -> None:
    provider = RestProvider(name="rest")
    provider.connect()
    result = provider.invoke(
        "fetch",
        resource_id="health/check",
        params={"base_url": rest_base_url},
    )
    assert result.success is True
    assert result.data["status_code"] == 200
    assert result.data["body"]["ok"] is True
    assert "/health/check" in result.data["body"]["path"]


def test_rest_provider_requires_base_url() -> None:
    provider = RestProvider(name="rest")
    result = provider.invoke("fetch", resource_id="relative/path")
    assert result.success is False
    assert "base_url" in (result.error or "").lower()
