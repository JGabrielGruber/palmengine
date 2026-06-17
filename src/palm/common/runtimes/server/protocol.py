"""
Server protocol — transport-agnostic request/response contracts.

Surfaces (REST, WebSocket, MCP, SSR) implement against these types so new
interaction models can be registered without changing the hosting runtime.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from palm.common.runtimes.server.registry import RouteRegistry

RouteHandler = Callable[["ServerRequest"], "ServerResponse | Awaitable[ServerResponse]"]


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"


@dataclass(frozen=True)
class ServerRequest:
    """Normalized inbound request independent of HTTP/WebSocket/MCP transport."""

    method: str
    path: str
    headers: Mapping[str, str] = field(default_factory=dict)
    body: dict[str, Any] | None = None
    query: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ServerResponse:
    """Normalized outbound response."""

    status: int
    body: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    content_type: str = "application/json"
    raw_body: bytes | None = None


@runtime_checkable
class ServerSurface(Protocol):
    """Extensible interaction model mounted on a :class:`~palm.common.runtimes.server.app.ServerApp`."""

    @property
    def name(self) -> str:
        """Registry name (e.g. ``rest``, ``websocket``, ``mcp``)."""

    @property
    def mount_prefix(self) -> str:
        """Optional URL prefix for all routes owned by this surface."""

    def register(self, registry: RouteRegistry) -> None:
        """Declare routes on the shared registry."""


def is_async_handler(handler: RouteHandler) -> bool:
    """Return whether ``handler`` is a coroutine function."""
    return inspect.iscoroutinefunction(handler)