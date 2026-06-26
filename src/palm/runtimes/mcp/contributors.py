"""Apply pattern- and application-owned MCP tool registrations."""

from __future__ import annotations

from typing import Any

from palm.app.mcp_registry import iter_app_mcp_contributors
from palm.patterns._apps import autoload as autoload_patterns
from palm.patterns._registry import installed_pattern_apps, iter_mcp_contributors


def register_pattern_mcp_tools(mcp: Any, rest_client: Any) -> None:
    """Autoload pattern apps and register contributed MCP tools."""
    autoload_patterns()
    for app in installed_pattern_apps():
        app.ready()
    for contributor in iter_mcp_contributors():
        contributor.register(mcp, rest_client)


def register_app_mcp_tools(mcp: Any, rest_client: Any) -> None:
    """Register application-owned MCP tools from the app contributor registry."""
    for contributor in iter_app_mcp_contributors():
        contributor.register(mcp, rest_client)


__all__ = ["register_app_mcp_tools", "register_pattern_mcp_tools"]