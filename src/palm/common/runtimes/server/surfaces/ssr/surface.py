"""
SSR surface — extension point for server-rendered interactive flows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.surfaces.base import BaseSurface

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


class SsrSurface(BaseSurface):
    """Placeholder surface for future server-side rendering of wizards and dashboards."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    @property
    def name(self) -> str:
        return "ssr"

    @property
    def mount_prefix(self) -> str:
        return "/ssr"

    def register(self, registry: RouteRegistry) -> None:
        registry.register(
            method="GET",
            path="/v1/surfaces/ssr",
            handler=self._info,
            surface=self.name,
        )

    def _info(self, request: ServerRequest) -> ServerResponse:
        return ServerResponse(
            status=501,
            body={
                "surface": self.name,
                "status": "planned",
                "detail": "SSR handlers will render interactive flows without a separate client.",
                "mount_prefix": self.mount_prefix,
            },
        )