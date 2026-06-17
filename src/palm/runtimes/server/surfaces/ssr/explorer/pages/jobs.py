"""Job list and context viewer pages."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.ssr.explorer.components import (
    action_button,
    action_list,
    code_block,
    data_table,
    event_timeline,
    invoke_chain,
    resource_timeline_table,
    stat_card,
)
from palm.runtimes.server.surfaces.ssr.explorer.resource_helpers import palm_invoke_chain
from palm.runtimes.server.surfaces.ssr.explorer.forms import job_input_form
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page
from .base import PageContext
from .utils import flash_banners, not_found_page, status_badge
from palm.common.runtimes.server.ssr.render import escape, html_response


class JobPages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx

    def catalog(self, request: ServerRequest) -> ServerResponse:
        jobs = self._ctx.fetch.list_jobs(limit=50)
        rows = [
            [
                f'<a href="/explorer/jobs/{escape(row.get("job_id", ""))}">{escape(row.get("job_id", ""))}</a>',
                status_badge(row.get("status", "")),
                escape(str(row.get("instance_id") or "—")),
            ]
            for row in jobs
        ]
        content = (
            '<section class="section">'
            f'<p class="btn-row">{action_button("/explorer/flows/submit", "Submit a flow")}</p>'
            f"{data_table(['Job', 'Status', 'Instance'], rows) if rows else '<p class=\"muted\">No jobs yet. Submit via the form or POST /v1/jobs.</p>'}"
            "</section>"
        )
        return html_response(
            explorer_page(
                title="Jobs",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/jobs",
                subtitle="Click a job for the rich context viewer and interactive input form.",
            )
        )

    def detail(self, request: ServerRequest, *, job_id: str) -> ServerResponse:
        context = self._ctx.fetch.get_job_context(job_id)
        if not context.get("found", True):
            return not_found_page(self._ctx.version, f"Job not found: {job_id}")

        instance = context.get("instance") or {}
        pattern = context.get("pattern") or {}
        prompt = pattern.get("prompt")
        status = context.get("status", "")

        input_form_html = ""
        if status == "WAITING_FOR_INPUT":
            input_form_html = (
                '<section class="section"><div class="panel"><h3>Provide input</h3>'
                f"{job_input_form(job_id, pattern)}"
                "</div></section>"
            )

        resource_invocations = context.get("resource_invocations") or {}
        resource_entries = resource_invocations.get("entries") or []
        palm_chain_html = ""
        chain = palm_invoke_chain(resource_entries if isinstance(resource_entries, list) else [])
        if chain:
            palm_chain_html = (
                '<section class="section"><div class="panel"><h3>Compositional invoke chain</h3>'
                f"{invoke_chain(chain)}"
                "</div></section>"
            )
        resource_timeline_html = ""
        if resource_entries:
            resource_timeline_html = (
                '<section class="section"><div class="panel"><h3>Resource invocations</h3>'
                f"{resource_timeline_table(resource_entries if isinstance(resource_entries, list) else [])}"
                "</div></section>"
            )

        content = (
            f"{flash_banners(request)}"
            '<section class="section"><div class="grid-3">'
            f"{stat_card('Status', status)}"
            f"{stat_card('Pattern', pattern.get('pattern', '—'))}"
            f"{stat_card('Step', pattern.get('step') or '—')}"
            "</div></section>"
            f"{input_form_html}"
            f"{palm_chain_html}"
            f"{resource_timeline_html}"
            '<section class="section"><div class="grid-2">'
            '<div class="panel"><h3>Interactive context</h3>'
            f"<p class=\"muted\">{escape(prompt) if prompt else 'No active prompt.'}</p>"
            f"{code_block(pattern)}"
            "</div>"
            '<div class="panel"><h3>Instance</h3>'
            f"<p><a href=\"/explorer/instances/{escape(instance.get('instance_id', ''))}\">"
            f"{escape(instance.get('instance_id', '—'))}</a></p>"
            f"{code_block(instance)}"
            "</div>"
            "</div></section>"
            '<section class="section"><div class="panel"><h3>Next actions</h3>'
            f"{action_list(context.get('next_actions') or [])}"
            "</div></section>"
            '<section class="section"><div class="grid-2">'
            '<div class="panel"><h3>Blackboard snapshot</h3>'
            f"{code_block(context.get('blackboard_snapshot') or {'note': 'No snapshots yet'})}"
            "</div>"
            '<div class="panel"><h3>Recent events</h3>'
            f"{event_timeline(context.get('recent_events') or [])}"
            "</div>"
            "</div></section>"
            '<section class="section"><div class="panel"><h3>Full context payload</h3>'
            f'<p class="muted">Backed by <code>GET /v1/jobs/{escape(job_id)}/context</code></p>'
            f"{code_block(context)}"
            "</div></section>"
        )
        return html_response(
            explorer_page(
                title=f"Job {job_id}",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/jobs",
                subtitle="Rich context assembled from live job state, projections, and snapshots.",
            )
        )