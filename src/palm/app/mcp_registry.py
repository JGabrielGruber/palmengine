"""
Application-level MCP contributor registry.

Downstream Palm applications (for example KnowKey) register optional MCP tools
alongside pattern-owned contributors.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

AppMcpRegisterFn = Callable[[Any, Any], None]


@dataclass(frozen=True)
class AppMcpContributor:
    """Application-owned MCP tools registered on the Palm operator adapter."""

    app_name: str
    register: AppMcpRegisterFn


_lock = threading.RLock()
_contributors: dict[str, AppMcpContributor] = {}


def register_app_mcp_contributor(contributor: AppMcpContributor) -> None:
    """Register application-owned MCP tools on the operator adapter."""
    with _lock:
        existing = _contributors.get(contributor.app_name)
        if existing is contributor:
            return
        _contributors[contributor.app_name] = contributor


def get_app_mcp_contributor(name: str) -> AppMcpContributor | None:
    """Return the MCP contributor for application ``name``, if registered."""
    with _lock:
        return _contributors.get(name)


def iter_app_mcp_contributors() -> list[AppMcpContributor]:
    """Return app MCP contributors in stable application-name order."""
    with _lock:
        return [_contributors[name] for name in sorted(_contributors)]


def clear_app_mcp_contributors() -> None:
    """Remove app MCP contributor registrations (primarily for tests)."""
    with _lock:
        _contributors.clear()


__all__ = [
    "AppMcpContributor",
    "AppMcpRegisterFn",
    "clear_app_mcp_contributors",
    "get_app_mcp_contributor",
    "iter_app_mcp_contributors",
    "register_app_mcp_contributor",
]