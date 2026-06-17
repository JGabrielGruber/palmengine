"""Process catalog pages."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.ssr.explorer.components import code_block, data_table
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page
from .base import PageContext
from .utils import not_found_page
from palm.common.runtimes.server.ssr.render import escape, html_response


class ProcessPages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx

    def catalog(self, request: ServerRequest) -> ServerResponse:
        processes = self._ctx.fetch.list_processes()
        rows = [
            [
                f'<a href="/explorer/processes/{escape(proc.definition_id)}">{escape(proc.name)}</a>',
                escape(str(len(proc.flows))),
                escape(proc.storage),
            ]
            for proc in processes
        ]
        content = (
            '<section class="section">'
            f"{data_table(['Name', 'Flows', 'Storage'], rows) if rows else '<p class=\"muted\">No processes registered.</p>'}"
            "</section>"
        )
        return html_response(
            explorer_page(
                title="Process Catalog",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/processes",
            )
        )

    def detail(self, request: ServerRequest, *, process_id: str) -> ServerResponse:
        process = self._ctx.fetch.get_process(process_id)
        if process is None:
            return not_found_page(self._ctx.version, f"Process not found: {process_id}")
        content = f'<section class="section"><div class="panel">{code_block(process.to_dict())}</div></section>'
        return html_response(
            explorer_page(
                title=process.name,
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/processes",
            )
        )