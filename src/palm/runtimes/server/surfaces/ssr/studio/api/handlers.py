"""Studio API handlers — palette and draft endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.ssr.studio.api.definitions import save_flow, save_process
from palm.runtimes.server.surfaces.ssr.studio.api.drafts import get_draft, list_drafts, save_draft
from palm.runtimes.server.surfaces.ssr.studio.api.extensions import get_extensions
from palm.runtimes.server.surfaces.ssr.studio.api.palette import get_palette
from palm.runtimes.server.surfaces.ssr.studio.api.templates import get_template, get_templates

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

    def extensions(self, request: ServerRequest) -> ServerResponse:
        return get_extensions(request)

    def save_flow(self, request: ServerRequest) -> ServerResponse:
        return save_flow(self._ctx, request)

    def save_process(self, request: ServerRequest) -> ServerResponse:
        return save_process(self._ctx, request)

    def list_templates(self, request: ServerRequest) -> ServerResponse:
        return get_templates(request)

    def get_template(self, request: ServerRequest, *, template_id: str) -> ServerResponse:
        return get_template(request, template_id=template_id)
