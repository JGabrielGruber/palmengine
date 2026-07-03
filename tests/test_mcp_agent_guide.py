"""Tests for bundled palm://agent/guide content."""

from __future__ import annotations

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402


class _GuideFakeClient:
    def list_waiting_jobs(self, *, limit: int = 50) -> dict:
        return {"jobs": []}

    def get_health(self) -> dict:
        return {"status": "ok"}


@pytest.fixture
def guide_server():
    config = PalmMcpConfig.from_env()
    assert config.llms_txt_path is not None
    server = create_mcp_server(config, client=_GuideFakeClient())
    return server


@pytest.mark.asyncio
async def test_agent_guide_uses_bundled_llms_txt(guide_server) -> None:
    async with Client(guide_server) as client:
        result = await client.read_resource("palm://agent/guide")
    text = "".join(block.text for block in result if hasattr(block, "text"))
    assert "Palm MCP Agent Guide" in text
    assert "Set PALM_LLMS_TXT" not in text


@pytest.mark.asyncio
async def test_agent_guide_prefers_mcp_txt_when_bundled(monkeypatch) -> None:
    """Bundled default serves the focused MCP operator guide."""
    monkeypatch.delenv("PALM_LLMS_TXT", raising=False)
    config = PalmMcpConfig.from_env()
    assert config.llms_txt_path is not None
    assert config.llms_txt_path.name in {"mcp.txt", "llms.txt"}
    if config.llms_txt_path.name == "mcp.txt":
        assert "Palm MCP Agent Guide" in config.llms_txt_path.read_text(encoding="utf-8")
