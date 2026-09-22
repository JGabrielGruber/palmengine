"""Palm MCP stdio adapter — FastMCP tools and resources over REST."""

from bundles.standard.runtimes.mcp.server import create_mcp_server, mcp

__all__ = ["create_mcp_server", "mcp", "main"]


def main() -> None:
    """Entry point for ``palm-mcp`` console script."""
    mcp.run()
