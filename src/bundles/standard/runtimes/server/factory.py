"""
Server factory — build :class:`ServerApp` and optional ApplicationHost bridges.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bundles.standard.app.settings import PalmSettings
from bundles.standard.runtimes.server.app import ServerApp, create_server_app
from bundles.standard.runtimes.server.context import ServerContext
from bundles.standard.runtimes.server.surfaces import default_surfaces

if TYPE_CHECKING:
    from bundles.standard.app.host.application_host import ApplicationHost
    from plugins.kits.server.webhooks import ServerWebhookBridge
    from bundles.standard.runtimes.server.runtime import ServerRuntime


def build_server_context(
    runtime: ServerRuntime,
    *,
    host: ApplicationHost | None = None,
    settings: PalmSettings | None = None,
) -> ServerContext:
    """Create a server context sharing the runtime plan registry.

    ``settings`` is used for host-less product build (analytics knobs, session
    policy). When ``host`` is attached, host settings win via the host surface.
    """
    return ServerContext(
        runtime,
        host=host,
        plan_registry=runtime.plan_registry,
        settings=settings,
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
    # Surfaces come from the context's composition (an attached host's, or the
    # standalone server shape). Explicit `surfaces=` still wins.
    resolved = surfaces if surfaces is not None else default_surfaces(ctx, only=ctx.composition.surfaces)
    return create_server_app(ctx, surfaces=resolved, webhook_bridge=webhook_bridge)
