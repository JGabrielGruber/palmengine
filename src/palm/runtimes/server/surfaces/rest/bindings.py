"""Shared REST handler binding helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.common.runtimes.server.protocol import RouteHandler


def bind_handler(ctx: Any, fn: Callable[..., Any]) -> RouteHandler:
    """Wrap a ``(ctx, request, **params)`` handler for the route registry."""

    def _handler(request: Any, **params: str) -> Any:
        return fn(ctx, request, **params)

    return _handler


__all__ = ["bind_handler"]