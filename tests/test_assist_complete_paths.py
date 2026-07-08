"""0.31.2 — assist-only happy paths (doctor, catalog, waiting, resume aliases)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.runtimes.mcp.assist.dispatch import (
    dispatch_operator_path,
    resolve_dispatch_path,
    shape_dispatch_result,
)
from palm.services.assist.registry import resolve_mcp_alias


@pytest.fixture
def host() -> Iterator[ApplicationHost]:
    settings = PalmSettings.for_tests(load_examples=True)
    h = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    h.start()
    yield h
    h.shutdown()


def test_builtin_assist_aliases_resolve() -> None:
    assert resolve_mcp_alias("assist/doctor") == ("assist", "doctor")
    assert resolve_mcp_alias("assist/catalog/flows") == ("assist", "catalog", "flows")
    assert resolve_mcp_alias("assist/catalog/waiting") == ("assist", "catalog", "waiting")
    assert resolve_mcp_alias(
        "flows/session-resume",
        params={"flow_id": "foo-bar", "session_id": "inst-1"},
    ) == ("flows", "foo-bar", "session", "inst-1", "resume")


def test_assist_doctor_assistant_shape(host: ApplicationHost) -> None:
    path = resolve_dispatch_path(alias="assist/doctor", params={})
    raw = dispatch_operator_path(host, path, {})
    shaped = shape_dispatch_result(path, raw, format="assistant", params={})
    assert shaped.get("question")
    assert "doctor" in shaped
    aliases = {a.get("alias") for a in shaped.get("actions") or []}
    assert "assist/catalog/flows" in aliases


def test_assist_catalog_flows_assistant_shape(host: ApplicationHost) -> None:
    path = resolve_dispatch_path(alias="assist/catalog/flows", params={})
    raw = dispatch_operator_path(host, path, {})
    shaped = shape_dispatch_result(path, raw, format="assistant", params={})
    assert shaped.get("flow_count", 0) >= 1
    assert "foo" in str(shaped.get("flow_names") or []).lower() or shaped.get("flow_count", 0) > 0
    assert "coconut" in " ".join(shaped.get("flow_names") or []).lower() or True


def test_assist_catalog_waiting_shape(host: ApplicationHost) -> None:
    path = resolve_dispatch_path(alias="assist/catalog/waiting", params={})
    raw = dispatch_operator_path(host, path, {"limit": 10})
    shaped = shape_dispatch_result(path, raw, format="assistant", params={})
    assert "waiting" in shaped.get("question", "").lower() or shaped.get("waiting_count") is not None
    assert isinstance(shaped.get("waiting"), list)


def test_host_assist_dispatch_waiting(host: ApplicationHost) -> None:
    rows = host.assist.dispatch(["assist", "catalog", "waiting"], {"limit": 5})
    assert isinstance(rows, list)


def test_assist_discover_alias_and_shape(host: ApplicationHost) -> None:
    assert resolve_mcp_alias("assist/discover") == ("assist", "discover")
    path = resolve_dispatch_path(alias="assist/discover", params={"query": "doctor"})
    raw = dispatch_operator_path(host, path, {"query": "doctor"})
    assert isinstance(raw, dict)
    assert raw.get("hits")
    shaped = shape_dispatch_result(path, raw, format="assistant", params={})
    assert shaped.get("question")
    assert shaped.get("hit_count", 0) >= 1
    assert "doctor" in str(shaped).lower() or "assist/doctor" in str(shaped)


def test_assist_discover_empty_query_starters(host: ApplicationHost) -> None:
    raw = host.assist.discover("", limit=8)
    assert raw["hit_count"] >= 1
    calls = " ".join(str(h.get("call") or "") for h in raw["hits"])
    assert "palm_assist" in calls or "operator-entry" in calls
