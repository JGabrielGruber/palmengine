"""Tests for palm://agent/skill and palm://agent/references/* MCP resources."""

from __future__ import annotations

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402


class _SkillFakeClient:
    def list_waiting_jobs(self, *, limit: int = 50) -> dict:
        return {"jobs": []}

    def get_health(self) -> dict:
        return {"status": "ok"}


@pytest.fixture
def skill_server():
    config = PalmMcpConfig.from_env()
    assert config.skill_root is not None
    server = create_mcp_server(config, client=_SkillFakeClient())
    return server


@pytest.mark.asyncio
async def test_agent_card_resource(skill_server) -> None:
    """L1 progressive guide (0.31.3)."""
    async with Client(skill_server) as client:
        result = await client.read_resource("palm://agent/card")
    text = "".join(block.text for block in result if hasattr(block, "text"))
    assert "palm_assist" in text
    assert "palm://agent/card" in text or "Load more" in text or "L1" in text
    assert len(text) < 4000  # keep card small vs full mcp.txt


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "uri,needle",
    [
        ("palm://agent/skill", "Palm Skill"),
        ("palm://agent/references/agent-guide", "Golden rule"),
        ("palm://agent/references/mcp-patterns", "call_connected_tool"),
        ("palm://agent/references/session-management", "Never assume state"),
        ("palm://agent/references/common-flows", "Todo Builder"),
        ("palm://agent/references/design-flows", "palm_design_propose_flow"),
        ("palm://agent/references/branching-flows", "route_on_answer"),
    ],
)
async def test_agent_skill_resources(skill_server, uri: str, needle: str) -> None:
    async with Client(skill_server) as client:
        result = await client.read_resource(uri)
    text = "".join(block.text for block in result if hasattr(block, "text"))
    assert needle in text
    assert "PALM_SKILL_DIR" not in text