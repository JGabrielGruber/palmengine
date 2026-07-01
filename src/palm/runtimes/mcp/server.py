"""FastMCP server — Palm operator tools via in-process services or REST."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.runtimes.mcp.config import PalmMcpConfig
from palm.runtimes.mcp.assist import register_assist_tools
from palm.runtimes.mcp.contributors import register_app_mcp_tools, register_pattern_mcp_tools
from palm.runtimes.mcp.definitions import register_definitions_tools
from palm.runtimes.mcp.flows import register_flow_tools
from palm.runtimes.mcp.prompts import register_core_prompts
from palm.runtimes.mcp.providers import register_provider_tools
from palm.runtimes.mcp.resources import register_core_resources
from palm.runtimes.mcp.rest_client import PalmRestClient, PalmRestError
from palm.runtimes.mcp.system import register_system_tools

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext

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
    ctx: ServerContext | None = None,
) -> FastMCP:
    """Build a FastMCP server wired to in-process services or a REST backend."""
    resolved = config or PalmMcpConfig.from_env()
    backend = _resolve_backend(resolved, client=client, ctx=ctx)
    mcp = FastMCP("Palm Operator")

    register_assist_tools(mcp, backend)
    register_flow_tools(mcp, backend)
    register_definitions_tools(mcp, backend)
    register_system_tools(mcp, backend)
    register_provider_tools(mcp, backend)
    register_core_resources(mcp, backend, config=resolved)
    register_core_prompts(mcp, resolved, backend)
    register_pattern_mcp_tools(mcp, backend)
    register_app_mcp_tools(mcp, backend)

    mcp._palm_client = backend  # type: ignore[attr-defined]
    mcp._palm_config = resolved  # type: ignore[attr-defined]
    return mcp


def _resolve_backend(
    config: PalmMcpConfig,
    *,
    client: Any | None,
    ctx: ServerContext | None,
) -> Any:
    if client is not None:
        return client
    if config.in_process or ctx is not None:
        from palm.runtimes.mcp.in_process import create_in_process_backend

        return create_in_process_backend(config, ctx=ctx)
    return PalmRestClient(config)


mcp = create_mcp_server()

__all__ = ["PalmRestError", "create_mcp_server", "mcp"]