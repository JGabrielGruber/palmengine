"""Tests for 0.16 per-domain MCP tool registration."""

from __future__ import annotations

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402


class _MinimalBackend:
    def flows_list(self) -> dict:
        return {"flows": [], "count": 0}

    def flows_describe(self, flow_id: str) -> dict:
        return {"flow_id": flow_id}

    def flows_create_session(self, flow_id: str, body: dict) -> dict:
        return {"session_id": "inst-1", "flow_id": flow_id}

    def flows_get_session(self, flow_id, session_id: str) -> dict:
        return {
            "session_id": session_id,
            "flow_id": flow_id or "demo",
            "status": "RUNNING",
            "detail": {
                "instance_id": session_id,
                "flow_name": "demo",
                "status": "RUNNING",
                "answers": {},
            },
        }

    def list_waiting_jobs(self, *, limit: int = 50) -> dict:
        return {"jobs": [], "count": 0}

    def get_health(self) -> dict:
        return {"status": "ok"}


@pytest.mark.asyncio
async def test_legacy_wizard_tools_removed() -> None:
    server = create_mcp_server(
        PalmMcpConfig(base_url="http://127.0.0.1:8080", subject="dev", llms_txt_path=None),
        client=_MinimalBackend(),
    )
    async with Client(server) as client:
        tools = await client.list_tools()
    names = {tool.name for tool in tools}
    assert "palm_flows_session" in names
    assert "palm_system_doctor" in names
    assert "palm_definitions_validate_flow" in names
    assert "palm_definitions_analyze_impact" in names
    assert "palm_definitions_migrate_instance" in names
    assert "palm_providers_invoke" in names
    assert "palm_wizard_input" not in names
    assert "palm_submit_wizard" not in names
    assert "palm_inspect_instance" not in names