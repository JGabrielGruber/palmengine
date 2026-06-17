"""
ServerApp — composable app factory mounting registered surfaces.
"""

from __future__ import annotations

import asyncio
from typing import Any

from palm.common.runtimes.server.context import ServerContext
from palm.common.runtimes.server.middleware import PALM_SUBJECT_HEADER, authenticate_request
from palm.common.runtimes.server.protocol import (
    RouteHandler,
    ServerRequest,
    ServerResponse,
    is_async_handler,
)
from palm.common.runtimes.server.registry import RouteRegistry, SurfaceRegistry
from palm.common.runtimes.server.responses import not_found, unauthorized
from palm.common.runtimes.server.webhooks import ServerWebhookBridge


class ServerApp:
    """
    Transport-agnostic Palm server application.

    Surfaces register routes on a shared :class:`RouteRegistry`. The app
    dispatches normalized :class:`ServerRequest` objects and supports both
    sync and async handlers.
    """

    def __init__(
        self,
        ctx: ServerContext,
        *,
        routes: RouteRegistry | None = None,
        surfaces: SurfaceRegistry | None = None,
        webhook_bridge: ServerWebhookBridge | None = None,
    ) -> None:
        self._ctx = ctx
        self._routes = routes or RouteRegistry()
        self._surfaces = surfaces or SurfaceRegistry()
        self.webhook_bridge = webhook_bridge or ServerWebhookBridge.from_context(ctx)
        ctx.webhook_bridge = self.webhook_bridge  # type: ignore[attr-defined]
        self._mount_surfaces()

    @property
    def context(self) -> ServerContext:
        return self._ctx

    @property
    def routes(self) -> RouteRegistry:
        return self._routes

    @property
    def surfaces(self) -> SurfaceRegistry:
        return self._surfaces

    def register_surface(self, surface: Any) -> None:
        self._surfaces.register(surface)
        surface.register(self._routes)

    def dispatch(self, request: ServerRequest) -> ServerResponse:
        return _run_handler(self._resolve(request), request)

    async def dispatch_async(self, request: ServerRequest) -> ServerResponse:
        handler, params = self._resolve(request)
        if is_async_handler(handler):
            response = await handler(request, **params)
            return response
        return handler(request, **params)

    def _resolve(self, request: ServerRequest) -> tuple[RouteHandler, dict[str, str]]:
        spec = self._routes.match(request.method, request.path)
        if spec is None:
            return _not_found_handler, {"path": request.path}

        if spec.auth_required and not authenticate_request(self._ctx.runtime, request.headers):
            return _unauthorized_handler, {}

        match = spec.pattern.match(_normalize_path(request.path))
        params = match.groupdict() if match is not None else {}
        return spec.handler, params

    def _mount_surfaces(self) -> None:
        for surface in self._surfaces.all():
            surface.register(self._routes)


def create_server_app(
    ctx: ServerContext,
    *,
    surfaces: list[Any] | None = None,
    webhook_bridge: ServerWebhookBridge | None = None,
) -> ServerApp:
    """
    Build a :class:`ServerApp` from explicitly provided surfaces.

    Use :func:`palm.runtimes.server.factory.create_app` to mount default Palm
    surfaces (REST, WebSocket, MCP, SSR) from the runtime package.
    """
    registry = SurfaceRegistry()
    for surface in surfaces or ():
        registry.register(surface)

    return ServerApp(
        ctx,
        surfaces=registry,
        webhook_bridge=webhook_bridge,
    )


def _run_handler(
    resolved: tuple[RouteHandler, dict[str, str]],
    request: ServerRequest,
) -> ServerResponse:
    handler, params = resolved
    if is_async_handler(handler):
        return asyncio.run(handler(request, **params))
    return handler(request, **params)


def _normalize_path(path: str) -> str:
    if not path.startswith("/"):
        path = f"/{path}"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path


def _not_found_handler(request: ServerRequest, *, path: str = "") -> ServerResponse:
    return not_found(path or request.path)


def _unauthorized_handler(request: ServerRequest) -> ServerResponse:
    return unauthorized(f"missing or invalid {PALM_SUBJECT_HEADER} header")
