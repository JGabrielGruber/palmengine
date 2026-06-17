"""Resource catalog pages."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.ssr.explorer.components import code_block, data_table
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page
from palm.common.runtimes.server.ssr.render import escape, html_response
from .base import PageContext
from .utils import not_found_page


class ResourcePages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx

    def catalog(self, request: ServerRequest) -> ServerResponse:
        entries = self._ctx.fetch.list_resource_catalog()
        rows = [
            [
                f'<a href="/explorer/resources/{escape(entry.definition_id)}">{escape(entry.name)}</a>',
                escape(entry.provider),
                escape(entry.action),
                escape(entry.summary()),
            ]
            for entry in entries
        ]
        content = (
            '<section class="section">'
            f"{data_table(['Name', 'Provider', 'Action', 'Detail'], rows) if rows else '<p class=\"muted\">No resources registered.</p>'}"
            "</section>"
        )
        return html_response(
            explorer_page(
                title="Resource Catalog",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/resources",
            )
        )

    def detail(self, request: ServerRequest, *, resource_id: str) -> ServerResponse:
        payload = self._ctx.fetch.describe_resource(resource_id)
        if payload is None:
            return not_found_page(self._ctx.version, f"Resource not found: {resource_id}")
        content = f'<section class="section"><div class="panel">{code_block(payload)}</div></section>'
        return html_response(
            explorer_page(
                title=str(payload.get("name", resource_id)),
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/resources",
            )
        )