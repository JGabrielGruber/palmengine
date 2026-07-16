"""
Server factory — build :class:`ServerApp` and optional ApplicationHost bridges.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.runtimes.server.app import ServerApp, create_server_app
from palm.runtimes.server.context import ServerContext
from palm.runtimes.server.surfaces import default_surfaces

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost
    from palm.common.runtimes.server.webhooks import ServerWebhookBridge
    from palm.runtimes.server.runtime import ServerRuntime


def build_server_context(
    runtime: ServerRuntime,
    *,
    host: ApplicationHost | None = None,
) -> ServerContext:
    """Create a server context sharing the runtime plan registry."""
    return ServerContext(
        runtime,
        host=host,
        plan_registry=runtime.plan_registry,
    )


def create_app(
    runtime: ServerRuntime,
    *,
    host: ApplicationHost | None = None,
    surfaces: list[Any] | None = None,
    webhook_bridge: ServerWebhookBridge | None = None,
) -> ServerApp:
    """Factory for a composable Palm server application with default surfaces."""
    ctx = build_server_context(runtime, host=host)
    # A host attached to the server contributes its CompositionProfile.surfaces;
    # standalone (no host) mounts all. Explicit `surfaces=` still wins.
    only = ctx.host.composition.surfaces if ctx.host is not None else None
    resolved = surfaces if surfaces is not None else default_surfaces(ctx, only=only)
    return create_server_app(ctx, surfaces=resolved, webhook_bridge=webhook_bridge)
