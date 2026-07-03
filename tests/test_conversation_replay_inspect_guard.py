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


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="0.22.1 protocol-only; engine does not block unsolicited yes yet (0.23.0)",
    strict=False,
)
async def test_unsolicited_yes_completes_without_user_intent(inspect_guard_ctx) -> None:
    """Documents tc4 from conversation_export.xml — blocked in 0.23.0 with input_token."""
    server, _backend = _mcp_server(inspect_guard_ctx)
    async with Client(server) as client:
        started = await client.call_tool("palm_assist", {})
        session_id = started.data["session_id"]
        await client.call_tool(
            "palm_assist",
            {"params": {"session_id": session_id, "value": "3"}},
        )
        after_choice = await client.call_tool(
            "palm_flows_session",
            {"session_id": session_id, "format": "assistant"},
        )
        if after_choice.data.get("mutation", {}).get("confirm_step"):
            await client.call_tool(
                "palm_assist",
                {"params": {"session_id": session_id, "value": "yes"}},
            )
        final = await client.call_tool(
            "palm_flows_session",
            {"session_id": session_id, "format": "assistant"},
        )
    assert final.data.get("status") != "complete"