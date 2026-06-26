"""FastMCP server — Palm operator tools and resources over REST."""

from __future__ import annotations

from typing import Any

from palm.runtimes.mcp.config import PalmMcpConfig
from palm.runtimes.mcp.contributors import register_app_mcp_tools, register_pattern_mcp_tools
from palm.runtimes.mcp.debug_tools import register_debug_tools
from palm.runtimes.mcp.phase5_tools import register_phase5_tools
from palm.runtimes.mcp.prompts import register_core_prompts
from palm.runtimes.mcp.resources import register_core_resources
from palm.runtimes.mcp.rest_client import PalmRestClient, PalmRestError
from palm.runtimes.mcp.tools import register_core_tools

try:
    from fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - optional extra
    raise ImportError(
        "fastmcp is required for the Palm MCP server. "
        'Install with: pip install "palmengine[mcp]"'
    ) from exc


def create_mcp_server(
    config: PalmMcpConfig | None = None,
    *,
    client: Any | None = None,
) -> FastMCP:
    """Build a FastMCP server wired to a Palm REST backend."""
    resolved = config or PalmMcpConfig.from_env()
    rest_client = client if client is not None else PalmRestClient(resolved)
    mcp = FastMCP("Palm Operator")

    register_core_tools(mcp, rest_client)
    register_core_resources(mcp, rest_client, config=resolved)
    register_core_prompts(mcp, resolved, rest_client)
    register_pattern_mcp_tools(mcp, rest_client)
    register_app_mcp_tools(mcp, rest_client)
    register_debug_tools(mcp, rest_client)
    register_phase5_tools(mcp, rest_client)

    mcp._palm_client = rest_client  # type: ignore[attr-defined]
    mcp._palm_config = resolved  # type: ignore[attr-defined]
    return mcp


mcp = create_mcp_server()

__all__ = ["PalmRestError", "create_mcp_server", "mcp"]