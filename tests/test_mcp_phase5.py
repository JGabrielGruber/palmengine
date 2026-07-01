"""Phase 5 MCP tests — invoke resource, compose status, app contributors."""

from __future__ import annotations

from typing import Any

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.app.mcp_registry import (  # noqa: E402
    AppMcpContributor,
    clear_app_mcp_contributors,
    get_app_mcp_contributor,
    register_app_mcp_contributor,
)
from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.contributors import register_app_mcp_tools  # noqa: E402
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402


class _Phase5FakeClient:
    def invoke_resource(self, body: dict[str, Any]) -> dict[str, Any]:
        return {
            "success": True,
            "resource_ref": body.get("resource_ref"),
            "action": body.get("action"),
        }

    def get_instance_tree(self, instance_id: str) -> dict[str, Any]:
        return {
            "instance_id": instance_id,
            "root": {"instance_id": instance_id, "flow": "main-menu", "step": "dispatch"},
            "focus": {"instance_id": instance_id, "flow": "main-menu", "step": "dispatch"},
            "active_child": {
                "instance_id": "inst-child",
                "flow": "capture-knowledge",
                "status": "WAITING_FOR_INPUT",
            },
            "links": {"explorer": f"http://127.0.0.1:8080/explorer/instances/{instance_id}"},
        }

    def flows_get_session(
        self,
        flow_id: str | None,
        session_id: str,
    ) -> dict[str, Any]:
        flat = self.get_wizard(session_id)
        return {
            "session_id": session_id,
            "flow_id": flow_id or flat.get("flow_name"),
            "status": flat.get("status"),
            "detail": flat,
        }

    def get_wizard(self, instance_id: str) -> dict[str, Any]:
        return {
            "instance_id": instance_id,
            "flow_name": "main-menu",
            "status": "WAITING_FOR_INPUT",
            "current_step_slug": "dispatch",
            "prompt": {
                "step": "dispatch",
                "step_kind": "resource",
                "waiting_for_child": True,
                "waiting_for_child_instance_id": "inst-child",
                "child_status": "WAITING_FOR_INPUT",
            },
            "answers": {"goal": "Compose docs", "menu_action": "capture_knowledge"},
            "next_actions": [{"action": "resume_child_wait"}],
        }

    def list_waiting_jobs(self, *, limit: int = 50) -> dict[str, Any]:
        return {"jobs": []}

    def get_health(self) -> dict[str, Any]:
        return {"status": "ok"}


@pytest.fixture
def phase5_server():
    fake = _Phase5FakeClient()
    server = create_mcp_server(
        PalmMcpConfig(base_url="http://127.0.0.1:8080", subject="dev", llms_txt_path=None),
        client=fake,
    )
    return server, fake


@pytest.mark.asyncio
async def test_palm_invoke_resource_tool(phase5_server) -> None:
    server, _ = phase5_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_providers_invoke",
            {
                "resource_ref": "fetch-customer",
                "action": "fetch",
                "params": {"customer_id": "42"},
            },
        )
    assert result.data["success"] is True
    assert result.data["resource_ref"] == "fetch-customer"


@pytest.mark.asyncio
async def test_palm_invoke_resource_rejects_mcp_uri(phase5_server) -> None:
    server, _ = phase5_server
    async with Client(server) as client:
        with pytest.raises(Exception, match="MCP read resource"):
            await client.call_tool(
                "palm_providers_invoke",
                {"resource_ref": "palm://definitions/flows"},
            )


@pytest.mark.asyncio
async def test_palm_compose_status_tool(phase5_server) -> None:
    server, _ = phase5_server
    async with Client(server) as client:
        result = await client.call_tool("palm_flows_compose_status", {"session_id": "inst-root"})
    assert result.data["flow"] == "main-menu"
    assert result.data["active_child"]["flow"] == "capture-knowledge"
    assert "goal" in result.data["answers_keys"]


@pytest.mark.asyncio
async def test_app_mcp_contributor_registers_tool(phase5_server) -> None:
    server, fake = phase5_server

    def _register(mcp: Any, rest_client: Any) -> None:
        @mcp.tool
        def demo_app_status() -> dict[str, str]:
            return {"app": "demo", "status": "ok"}

    previous = get_app_mcp_contributor("demo")
    register_app_mcp_contributor(AppMcpContributor(app_name="demo", register=_register))
    try:
        register_app_mcp_tools(server, fake)
        async with Client(server) as client:
            result = await client.call_tool("demo_app_status", {})
        assert result.data["app"] == "demo"
    finally:
        clear_app_mcp_contributors()
        if previous is not None:
            register_app_mcp_contributor(previous)
