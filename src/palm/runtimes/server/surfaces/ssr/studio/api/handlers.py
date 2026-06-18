"""Studio API handlers — palette and draft endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.ssr.studio.api.drafts import get_draft, list_drafts, save_draft
from palm.runtimes.server.surfaces.ssr.studio.api.palette import get_palette

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse


class StudioApiHandlers:
    """HTTP handlers for Studio JSON APIs."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    def palette(self, request: ServerRequest) -> ServerResponse:
        return get_palette(self._ctx, request)

    def list_drafts(self, request: ServerRequest) -> ServerResponse:
        return list_drafts(request)

    def get_draft(self, request: ServerRequest, *, draft_id: str) -> ServerResponse:
        return get_draft(request, draft_id=draft_id)

    def save_draft(self, request: ServerRequest) -> ServerResponse:
        return save_draft(request)