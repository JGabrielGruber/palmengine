"""Palm Studio page handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.render import html_response
from palm.runtimes.server.surfaces.ssr.studio.assets import (
    file_response,
    index_asset,
    resolve_asset,
)
from palm.runtimes.server.surfaces.ssr.studio.bootstrap import render_shell

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


class StudioPages:
    """HTTP handlers for the Studio SPA and its static assets."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    def index(self, request: ServerRequest) -> ServerResponse:
        html = render_shell(self._ctx, index_asset())
        return html_response(html)

    def assets_file(self, request: ServerRequest, *, filename: str) -> ServerResponse:
        return self._serve(f"assets/{filename}")

    def icons_file(self, request: ServerRequest, *, filename: str) -> ServerResponse:
        return self._serve(f"icons/{filename}")

    def root_file(self, request: ServerRequest, *, filename: str) -> ServerResponse:
        return self._serve(filename)

    def _serve(self, relative_path: str) -> ServerResponse:
        asset = resolve_asset(relative_path)
        if asset is None:
            return ServerResponse(status=404, body={"error": "not_found"})
        return file_response(asset)