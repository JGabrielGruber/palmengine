"""Replay bar from archive/conversation_export.xml — inspect must not auto-commit."""

from __future__ import annotations

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.app.bootstrap import load_definitions_for_repository  # noqa: E402
from palm.app.settings import PalmSettings  # noqa: E402
from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.in_process import PalmInProcessBackend, shutdown_in_process_runtime  # noqa: E402
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402
from palm.runtimes.server import ServerRuntime  # noqa: E402
from palm.runtimes.server.factory import build_server_context  # noqa: E402


@pytest.fixture
def inspect_guard_ctx():
    shutdown_in_process_runtime()
    settings = PalmSettings.for_tests(load_examples=True)
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(http=False)
    load_definitions_for_repository(rt.repository, settings)
    ctx = build_server_context(rt)
    yield ctx
    rt.stop()
    shutdown_in_process_runtime()


def _mcp_server(ctx) -> tuple:
    backend = PalmInProcessBackend(ctx)
    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
    )
    return create_mcp_server(config, client=backend), backend


@pytest.mark.asyncio
async def test_operator_entry_intent_has_mutation_envelope(inspect_guard_ctx) -> None:
    """After bare palm_assist(), intent step must expose mutations_allowed without confirm_step."""
    server, _backend = _mcp_server(inspect_guard_ctx)
    async with Client(server) as client:
        started = await client.call_tool("palm_assist", {})
        session_id = started.data["session_id"]
        inspect = await client.call_tool(
            "palm_flows_session",
            {"session_id": session_id, "format": "assistant"},
        )
    payload = inspect.data
    mutation = payload.get("mutation") or {}
    assert mutation.get("mutations_allowed") is True
    assert mutation.get("confirm_step") is not True
    assert mutation.get("step_slug") == "intent"
    assert mutation.get("input_token")


@pytest.mark.asyncio
async def test_inspect_only_path_stays_at_catalog_not_summary(
    inspect_guard_ctx,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replay inspect-only menu path — must not reach summary without explicit drive."""
    monkeypatch.setenv("PALM_MCP_REQUIRE_INPUT_TOKEN", "1")
    monkeypatch.setenv("PALM_MUTATION_SECRET", "test-secret")
    server, _backend = _mcp_server(inspect_guard_ctx)
    async with Client(server) as client:
        started = await client.call_tool("palm_assist", {})
        session_id = started.data["session_id"]
        inspect = await client.call_tool(
            "palm_flows_session",
            {"session_id": session_id, "format": "assistant"},
        )
        token = inspect.data.get("mutation", {}).get("input_token")
        await client.call_tool(
            "palm_assist",
            {"params": {"session_id": session_id, "value": "3", "input_token": token}},
        )
        after = await client.call_tool(
            "palm_flows_session",
            {"session_id": session_id, "format": "assistant"},
        )
    mutation = after.data.get("mutation") or {}
    assert after.data.get("status") == "waiting"
    assert mutation.get("step_slug") == "catalog"
    assert mutation.get("confirm_step") is not True


@pytest.mark.asyncio
async def test_unsolicited_write_blocked_in_strict_mode(
    inspect_guard_ctx,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Documents tc4 from conversation_export.xml — blocked in 0.23.0 with input_token."""
    monkeypatch.setenv("PALM_MCP_REQUIRE_INPUT_TOKEN", "1")
    monkeypatch.setenv("PALM_MUTATION_SECRET", "test-secret")
    server, _backend = _mcp_server(inspect_guard_ctx)
    async with Client(server) as client:
        started = await client.call_tool("palm_assist", {})
        session_id = started.data["session_id"]
        with pytest.raises(Exception, match="mutation_rejected"):
            await client.call_tool(
                "palm_assist",
                {"params": {"session_id": session_id, "value": "3"}},
            )
        final = await client.call_tool(
            "palm_flows_session",
            {"session_id": session_id, "format": "assistant"},
        )
    assert final.data.get("status") == "waiting"
    assert final.data.get("mutation", {}).get("step_slug") == "intent"