"""Tests for stable ``palm_assist`` MCP dispatch tool."""

from __future__ import annotations

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.app.settings import PalmSettings  # noqa: E402
from palm.runtimes.mcp.assist.dispatch import (  # noqa: E402
    assist_routes_payload,
    resolve_dispatch_path,
)
from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.in_process import (  # noqa: E402
    PalmInProcessBackend,
    shutdown_in_process_runtime,
)
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402
from palm.runtimes.server import ServerRuntime  # noqa: E402
from palm.runtimes.server.factory import build_server_context  # noqa: E402


@pytest.fixture
def assist_server_ctx():
    from palm.app.bootstrap import load_definitions_for_repository

    shutdown_in_process_runtime()
    settings = PalmSettings.for_tests(load_examples=True)
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(http=False)
    load_definitions_for_repository(rt.repository, settings)
    ctx = build_server_context(rt)
    yield ctx
    rt.stop()
    shutdown_in_process_runtime()


def _register_operator_entry_contributor() -> None:
    import examples.definitions.operator_entry as operator_entry

    operator_entry.register_definitions(object())


def test_resolve_operator_entry_start_alias() -> None:
    _register_operator_entry_contributor()
    path = resolve_dispatch_path(alias="operator-entry/start")
    assert path == ["assist", "scenarios", "operator-entry", "start"]


def test_assist_routes_resource_includes_aliases() -> None:
    _register_operator_entry_contributor()
    catalog = assist_routes_payload()
    aliases = {entry["alias"] for entry in catalog["aliases"]}
    assert "operator-entry/start" in aliases
    assert any(route["domain"] == "assist" for route in catalog["routes"])


@pytest.mark.asyncio
async def test_palm_assist_starts_operator_entry(assist_server_ctx) -> None:
    backend = PalmInProcessBackend(assist_server_ctx)
    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
    )
    server = create_mcp_server(config, client=backend)

    async with Client(server) as client:
        result = await client.call_tool(
            "palm_assist",
            {"path": ["assist", "scenarios", "operator-entry", "start"], "params": {}},
        )

    payload = result.data
    assert payload.get("session_id")
    assert payload.get("question")
    assert payload.get("path") == ["assist", "scenarios", "operator-entry", "start"]


@pytest.mark.asyncio
async def test_palm_assist_alias_start(assist_server_ctx) -> None:
    backend = PalmInProcessBackend(assist_server_ctx)
    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
    )
    server = create_mcp_server(config, client=backend)

    async with Client(server) as client:
        result = await client.call_tool(
            "palm_assist",
            {"alias": "operator-entry/start", "params": {}},
        )

    assert result.data.get("session_id")


def test_in_process_assist_dispatch_doctor(assist_server_ctx) -> None:
    backend = PalmInProcessBackend(assist_server_ctx)
    report = backend.assist_dispatch(["assist", "doctor"])
    assert isinstance(report, dict)


@pytest.mark.asyncio
async def test_palm_assist_assist_session_returns_assistant(assist_server_ctx) -> None:
    backend = PalmInProcessBackend(assist_server_ctx)
    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
    )
    server = create_mcp_server(config, client=backend)

    async with Client(server) as client:
        started = await client.call_tool(
            "palm_assist",
            {"alias": "operator-entry/start", "params": {}},
        )
        session_id = started.data["session_id"]
        result = await client.call_tool(
            "palm_assist",
            {
                "path": ["assist", "session", session_id],
                "params": {},
            },
        )

    payload = result.data
    assert payload.get("session_id") == session_id
    assert payload.get("question")
    assert payload.get("status") == "waiting"
    assert "detail" not in payload
    assert "operator_hint" not in payload