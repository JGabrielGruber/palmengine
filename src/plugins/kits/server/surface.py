"""
Base surface — shared abstract base for server interaction models.

A composition root mounts concrete surfaces (REST, WebSocket, MCP, SSR).
Those surfaces implement this base and live with the runtime that wires them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plugins.kits.server.registry import RouteRegistry


class BaseSurface(ABC):
    """Convenience base for surfaces that register HTTP-style routes."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Surface registry name."""

    @property
    def mount_prefix(self) -> str:
        return ""

    @abstractmethod
    def register(self, registry: RouteRegistry) -> None:
        """Declare routes on the shared registry."""
