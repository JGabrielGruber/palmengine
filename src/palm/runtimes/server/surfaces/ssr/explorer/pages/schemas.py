"""Schema explorer page."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.render import escape, html_response
from palm.runtimes.server.surfaces.ssr.explorer.components import badge, code_block
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page

from .base import PageContext


class SchemaPages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx

    def catalog(self, request: ServerRequest) -> ServerResponse:
        schemas = self._ctx.fetch.list_schemas()
        panels = []
        for item in schemas:
            panels.append(
                '<div class="panel">'
                f"<h3>{escape(item['flow_name'])} <span class=\"muted\">({escape(item['flow_id'])})</span></h3>"
                f"<p>{badge(str(item['kind']))}</p>"
                f"{code_block(item.get('schema') or {'ref': item.get('schema_ref')})}"
                "</div>"
            )
        content = (
            '<section class="section">'
            f'{"".join(panels) if panels else "<p class=\"muted\">No flow schemas configured.</p>"}'
            "</section>"
        )
        return html_response(
            explorer_page(
                title="Schema Explorer",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/schemas",
            )
        )
