"""Pattern registry page."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.ssr.explorer.components import data_table
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page
from .base import PageContext
from palm.common.runtimes.server.ssr.render import escape, html_response


class PatternPages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx

    def catalog(self, request: ServerRequest) -> ServerResponse:
        patterns = self._ctx.fetch.list_patterns()
        rows = [
            [f"<code>{escape(item['name'])}</code>", escape(item["class"]), escape(item["summary"])]
            for item in patterns
        ]
        content = f'<section class="section">{data_table(["Pattern", "Class", "Summary"], rows)}</section>'
        return html_response(
            explorer_page(
                title="Pattern Registry",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/patterns",
                subtitle="Installed behavior-tree patterns from palm.patterns.",
            )
        )