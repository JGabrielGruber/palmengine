"""Replay bar: weak-LLM todo-builder path inspired by session 019f1e9c."""

from __future__ import annotations

from typing import Any

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.app.settings import PalmSettings  # noqa: E402
from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.in_process import (  # noqa: E402
    PalmInProcessBackend,
    shutdown_in_process_runtime,
)
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402
from palm.runtimes.server import ServerRuntime  # noqa: E402
from palm.runtimes.server.factory import build_server_context  # noqa: E402

_MAX_REPLAY_TOOL_CALLS = 18


@pytest.fixture
def replay_server_ctx():
    from palm.app.bootstrap import load_definitions_for_repository
    import examples.definitions.operator_entry as operator_entry

    shutdown_in_process_runtime()
    settings = PalmSettings.for_tests(load_examples=True)
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(http=False)
    load_definitions_for_repository(rt.repository, settings)
    operator_entry.register_definitions(rt.repository)
    ctx = build_server_context(rt)
    yield ctx
    rt.stop()
    shutdown_in_process_runtime()


def _session_id(payload: dict[str, Any]) -> str:
    sid = payload.get("session_id") or payload.get("instance_id")
    assert sid, f"expected session id in {payload!r}"
    return str(sid)


def _status(payload: dict[str, Any]) -> str:
    return str(payload.get("status") or "").upper()


async def _assist(client: Client, **kwargs: Any) -> dict[str, Any]:
    result = await client.call_tool("palm_assist", kwargs)
    assert not result.is_error, getattr(result, "error", result)
    return result.data


async def _add_todo_item(
    client: Client,
    *,
    flow_sid: str,
    title: str,
    priority: str = "medium",
) -> None:
    await _assist(
        client,
        params={
            "session_id": flow_sid,
            "flow_id": "todo-builder",
            "collection_action": "add",
            "value": title,
        },
    )
    await _assist(
        client,
        params={"session_id": flow_sid, "flow_id": "todo-builder", "value": ""},
    )
    await _assist(
        client,
        params={"session_id": flow_sid, "flow_id": "todo-builder", "value": priority},
    )


@pytest.mark.asyncio
async def test_replay_todo_builder_weak_llm_path(replay_server_ctx) -> None:
    backend = PalmInProcessBackend(replay_server_ctx)
    server = create_mcp_server(
        PalmMcpConfig(
            base_url="http://127.0.0.1:8080",
            subject="dev",
            llms_txt_path=None,
            in_process=True,
        ),
        client=backend,
    )

    tool_calls = 0
    final: dict[str, Any] = {}

    async with Client(server) as client:
        started = await _assist(client)
        tool_calls += 1
        assist_sid = _session_id(started)

        picked = await _assist(
            client,
            params={"session_id": assist_sid, "value": "todo-builder"},
        )
        tool_calls += 1
        if _status(picked) == "WAITING":
            await _assist(client, params={"session_id": assist_sid, "value": "yes"})
            tool_calls += 1

        handoff = await _assist(
            client,
            alias="operator-entry/handoff",
            params={"session_id": assist_sid},
        )
        tool_calls += 1
        assert handoff["handoff"]["flow_id"] == "todo-builder"

        created = await _assist(
            client,
            path=["flows", "todo-builder", "create"],
            params={},
        )
        tool_calls += 1
        flow_sid = _session_id(created)

        await _add_todo_item(client, flow_sid=flow_sid, title="Test Palm")
        tool_calls += 3
        await _add_todo_item(
            client,
            flow_sid=flow_sid,
            title="Drinking coffee",
            priority="high",
        )
        tool_calls += 3

        await _assist(
            client,
            params={
                "session_id": flow_sid,
                "flow_id": "todo-builder",
                "edit": {"item_index": 0, "priority": "low"},
            },
        )
        tool_calls += 1

        done = await _assist(
            client,
            params={
                "session_id": flow_sid,
                "flow_id": "todo-builder",
                "input": "continue",
            },
        )
        tool_calls += 1

        if _status(done) == "WAITING":
            await _assist(
                client,
                params={"session_id": flow_sid, "flow_id": "todo-builder", "value": "yes"},
            )
            tool_calls += 1

        final = await _assist(
            client,
            params={"session_id": flow_sid, "flow_id": "todo-builder"},
        )
        tool_calls += 1

        if _status(final) == "WAITING":
            committed = await _assist(
                client,
                params={"session_id": flow_sid, "flow_id": "todo-builder", "value": "yes"},
            )
            tool_calls += 1
            final = committed
    assert tool_calls <= _MAX_REPLAY_TOOL_CALLS, f"used {tool_calls} tool calls"
    assert _status(final) in {"SUCCEEDED", "SUCCESS", "COMPLETE"}, final