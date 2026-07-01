"""Assist scenario catalog and assistant session workspace pages."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.render import escape, html_response
from palm.runtimes.server.surfaces.ssr.explorer.components import (
    action_button,
    assist_workspace,
    data_table,
    link_card,
)
from palm.runtimes.server.surfaces.ssr.explorer.forms import assist_start_form
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page

from .base import PageContext
from .utils import flash_banners, not_found_page


class AssistPages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx

    def catalog(self, request: ServerRequest) -> ServerResponse:
        scenarios = self._ctx.fetch.list_assist_scenarios()
        rows = [
            [
                f'<a href="/explorer/assist/scenarios/{escape(row["scenario_id"])}">'
                f'{escape(str(row.get("scenario_id", "")))}</a>',
                escape(str(row.get("flow_id", ""))),
                escape(str(row.get("summary", ""))),
                action_button(
                    f"/explorer/assist/scenarios/{escape(row['scenario_id'])}",
                    "Open",
                ),
            ]
            for row in scenarios
        ]
        cards = "".join(
            link_card(
                f"/explorer/assist/scenarios/{escape(row['scenario_id'])}",
                str(row.get("scenario_id", "Scenario")),
                str(row.get("summary") or "Conversational operator guidance"),
            )
            for row in scenarios
        )
        content = (
            '<section class="section">'
            "<h2>Guided entry</h2>"
            '<p class="muted">Assist scenarios provide human-first operator guidance — '
            "question, numbered choices, and handoff into business flows.</p>"
            f"{flash_banners(request)}"
            f'<div class="grid-2">{cards}</div>'
            "</section>"
            '<section class="section"><h2>All scenarios</h2>'
            f"{data_table(['Scenario', 'Flow', 'Summary', ''], rows) if rows else '<p class=\"muted\">No assist scenarios registered.</p>'}"
            "</section>"
        )
        return html_response(
            explorer_page(
                title="Assist",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/assist",
                subtitle="Conversational operator guidance with assistant-shaped turns.",
            )
        )

    def scenario_detail(self, request: ServerRequest, *, scenario_id: str) -> ServerResponse:
        try:
            scenario = self._ctx.fetch.describe_assist_scenario(scenario_id)
        except Exception:
            return not_found_page(self._ctx.version, f"Assist scenario not found: {scenario_id}")

        flow = scenario.get("flow") or {}
        flow_name = flow.get("name") or scenario.get("flow_id") or "—"
        content = (
            '<section class="section">'
            f"<h2>{escape(scenario_id)}</h2>"
            f'<p class="muted">{escape(str(scenario.get("summary") or ""))}</p>'
            f"{flash_banners(request)}"
            '<div class="panel">'
            f"<p><strong>Flow:</strong> {escape(str(flow_name))}</p>"
            f"<p><strong>Contributor:</strong> {escape(str(scenario.get('contributor_id', '—')))}</p>"
            f"{assist_start_form(scenario_id)}"
            "</div>"
            f'<p class="btn-row">{action_button("/explorer/assist", "Back to catalog", tone="default")}</p>'
            "</section>"
        )
        return html_response(
            explorer_page(
                title=f"Assist — {scenario_id}",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/assist",
                subtitle="Start a guided assist session.",
            )
        )

    def session(self, request: ServerRequest, *, session_id: str) -> ServerResponse:
        try:
            view = self._ctx.fetch.get_assist_session(session_id)
        except Exception:
            return not_found_page(self._ctx.version, f"Assist session not found: {session_id}")

        from palm.runtimes.server.surfaces.ssr.explorer.pages.utils import query_message

        workspace = assist_workspace(
            session_id,
            view,
            notice=query_message(request, "notice"),
            error=query_message(request, "error"),
        )
        content = (
            '<section class="section">'
            f'<p class="btn-row">{action_button("/explorer/assist", "Assist catalog", tone="default")}</p>'
            f"{workspace}"
            "</section>"
        )
        return html_response(
            explorer_page(
                title="Assist session",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/assist",
                subtitle="Assistant envelope — question, choices, and compose context.",
            )
        )