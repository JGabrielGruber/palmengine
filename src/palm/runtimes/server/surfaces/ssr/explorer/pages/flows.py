"""Flow catalog, detail, and submission pages."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.render import escape, html_response
from palm.runtimes.server.surfaces.ssr.explorer.components import (
    action_button,
    badge,
    code_block,
    data_table,
    invoke_chain,
)
from palm.runtimes.server.surfaces.ssr.explorer.forms import flow_submit_form
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page
from palm.runtimes.server.surfaces.ssr.explorer.resource_helpers import (
    resource_href,
    wizard_resource_steps,
)

from .base import PageContext
from .utils import (
    flash_banners,
    flow_description,
    not_found_page,
    query_flow_id,
    start_flow_href,
)


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
            f'<p class="btn-row">{action_button("/explorer/flows/submit", "Start a flow")}</p>'
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
            "<h3>Start a registered flow</h3>"
            '<p class="muted">Select a flow from your repository and click <strong>Start this flow</strong>. '
            'Use <strong>Start</strong> on the <a href="/explorer/flows">flow catalog</a> to pre-fill your selection.</p>'
            f"{flash_banners(request)}"
            f"{flow_submit_form(flows, selected_flow_id=selected or None)}"
            "</div></section>"
        )
        return html_response(
            explorer_page(
                title="Start Flow",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/flows",
                subtitle="Primary path: registered definitions. Advanced test wizard available below.",
            )
        )

    def detail(self, request: ServerRequest, *, flow_id: str) -> ServerResponse:
        flow = self._ctx.fetch.get_flow(flow_id)
        if flow is None:
            return not_found_page(self._ctx.version, f"Flow not found: {flow_id}")

        resource_steps_html = ""
        if flow.pattern == "wizard":
            resource_steps = wizard_resource_steps(flow)
            if resource_steps:
                rows = []
                for step in resource_steps:
                    ref = str(step.get("resource_ref") or "—")
                    provider_label = "resource"
                    if ref != "—":
                        described = self._ctx.fetch.describe_resource(ref)
                        if described:
                            provider_label = str(described.get("provider") or "resource")
                    action = str(step.get("resource_action") or step.get("action") or "default")
                    params = step.get("params") or {}
                    param_summary = (
                        ", ".join(f"{k}={v}" for k, v in params.items()) if params else "—"
                    )
                    ref_link = (
                        f'<a href="{resource_href(ref)}">{escape(ref)}</a>' if ref != "—" else "—"
                    )
                    badge_html = badge(provider_label, tone="default")
                    rows.append(
                        [
                            escape(str(step.get("slug") or "—")),
                            ref_link,
                            badge_html,
                            escape(action),
                            f"<code>{escape(param_summary)}</code>",
                        ]
                    )
                palm_chain = invoke_chain(
                    [
                        {
                            "label": str(step.get("resource_ref") or step.get("slug")),
                            "action": step.get("resource_action") or "submit_flow",
                            "depth": index,
                        }
                        for index, step in enumerate(resource_steps)
                        if str(step.get("resource_ref", "")).startswith("submit-")
                        or (step.get("params") or {}).get("wait")
                    ]
                )
                resource_steps_html = (
                    '<section class="section"><div class="panel">'
                    "<h3>Resource steps</h3>"
                    f"{data_table(['Step', 'Resource', 'Provider', 'Action', 'Params'], rows)}"
                    '<h4>Compositional chain</h4>'
                    f"{palm_chain}"
                    "</div></section>"
                )

        content = (
            '<section class="section">'
            f'<p class="btn-row">{action_button(start_flow_href(flow.definition_id), "Start this flow")}</p>'
            "</section>"
            f"{resource_steps_html}"
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
