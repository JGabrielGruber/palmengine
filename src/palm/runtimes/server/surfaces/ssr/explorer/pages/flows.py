"""Flow catalog, detail, and submission pages."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.ssr.explorer.components import action_button, badge, code_block, data_table
from palm.runtimes.server.surfaces.ssr.explorer.forms import flow_submit_form
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page
from .base import PageContext
from .utils import (
    flash_banners,
    flow_description,
    not_found_page,
    query_flow_id,
    start_flow_href,
)
from palm.common.runtimes.server.ssr.render import escape, html_response


class FlowPages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx

    def catalog(self, request: ServerRequest) -> ServerResponse:
        flows = self._ctx.fetch.list_flows()
        rows = [
            [
                f'<a href="/explorer/flows/{escape(flow.definition_id)}">{escape(flow.name)}</a>',
                escape(flow.pattern),
                escape(flow_description(flow)),
                action_button(start_flow_href(flow.definition_id), "Start"),
            ]
            for flow in flows
        ]
        content = (
            '<section class="section">'
            f'<p class="btn-row">{action_button("/explorer/flows/submit", "Submit any flow")}</p>'
            f"{data_table(['Name', 'Pattern', 'Description', ''], rows) if rows else '<p class=\"muted\">No flows registered.</p>'}"
            "</section>"
        )
        return html_response(
            explorer_page(
                title="Flow Catalog",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/flows",
                subtitle="Registered flow definitions from the repository.",
            )
        )

    def submit(self, request: ServerRequest) -> ServerResponse:
        flows = self._ctx.fetch.list_flows()
        selected = query_flow_id(request)
        content = (
            '<section class="section"><div class="panel">'
            "<h3>Start a job</h3>"
            "<p class=\"muted\">Pick a registered flow from the dropdown, or switch to inline wizard mode. "
            "For advanced payloads use <code>POST /v1/jobs</code>.</p>"
            f"{flash_banners(request)}"
            f"{flow_submit_form(flows, selected_flow_id=selected or None)}"
            "</div></section>"
        )
        return html_response(
            explorer_page(
                title="Submit Flow",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/flows",
                subtitle="Schema-driven flow submission for common operator actions.",
            )
        )

    def detail(self, request: ServerRequest, *, flow_id: str) -> ServerResponse:
        flow = self._ctx.fetch.get_flow(flow_id)
        if flow is None:
            return not_found_page(self._ctx.version, f"Flow not found: {flow_id}")
        content = (
            '<section class="section">'
            f'<p class="btn-row">{action_button(start_flow_href(flow.definition_id), "Start this flow")}</p>'
            "</section>"
            '<section class="section"><div class="panel">'
            f"<p>{badge(flow.pattern)} {badge('schema' if flow.has_state_schema else 'no schema', tone='default')}</p>"
            f"<p class=\"muted\">{escape(flow_description(flow))}</p>"
            f"{code_block(flow.to_dict())}"
            "</div></section>"
        )
        return html_response(
            explorer_page(
                title=flow.name,
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/flows",
                subtitle=f"Definition id: {flow.definition_id}",
            )
        )