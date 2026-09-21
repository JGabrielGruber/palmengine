"""Apply pattern- and application-owned MCP tool registrations."""

from __future__ import annotations

from typing import Any

from palm.app.bootstrap import ensure_plugins
from palm.app.host.composition import composition_profile_from_name
from palm.app.mcp_registry import iter_app_mcp_contributors
from palm.common.patterns._registry import iter_mcp_contributors


def register_pattern_mcp_tools(mcp: Any, rest_client: Any) -> None:
    """Install the ``mcp`` record's packages and register contributed MCP tools.

    ``PatternApp.register`` already calls ``ready()``. This path drains the
    MCP contributor registry after that install.
    """
    ensure_plugins(composition_profile_from_name("mcp"))
    for contributor in iter_mcp_contributors():
        contributor.register(mcp, rest_client)


def register_app_mcp_tools(mcp: Any, rest_client: Any) -> None:
    """Register application-owned MCP tools from the app contributor registry."""
    for contributor in iter_app_mcp_contributors():
        contributor.register(mcp, rest_client)


__all__ = ["register_app_mcp_tools", "register_pattern_mcp_tools"]
