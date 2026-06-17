"""Wiki page handlers — overview, catalog, job context, and schema explorers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.components import (
    action_list,
    badge,
    code_block,
    data_table,
    event_timeline,
    link_card,
    stat_card,
)
from palm.common.runtimes.server.ssr.fetch import SsrFetcher
from palm.common.runtimes.server.ssr.layout import wiki_page
from palm.common.runtimes.server.ssr.render import escape, html_response

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


class WikiPages:
    """Server-rendered wiki routes backed by CQRS read models."""

    def __init__(self, ctx: ServerContext) -> None:
        self._fetch = SsrFetcher(ctx)

    def overview(self, request: ServerRequest) -> ServerResponse:
        flows = self._fetch.list_flows()
        processes = self._fetch.list_processes()
        patterns = self._fetch.list_patterns()
        jobs = self._fetch.list_jobs(limit=20)
        content = (
            '<section class="section"><div class="grid-3">'
            f"{stat_card('Flows', len(flows), hint='Registered definitions')}"
            f"{stat_card('Processes', len(processes), hint='Multi-flow bundles')}"
            f"{stat_card('Patterns', len(patterns), hint='Installed BT patterns')}"
            f"{stat_card('Jobs', len(jobs), hint='Live orchestration')}"
            "</div></section>"
            '<section class="section"><h2>Explore</h2><div class="grid-2">'
            f'{link_card("/wiki/flows", "Flow catalog", "Browse wizard, DAG, and pipeline definitions.")}'
            f'{link_card("/wiki/jobs", "Job context viewer", "Rich interactive state via /v1/jobs/{{id}}/context.")}'
            f'{link_card("/wiki/patterns", "Pattern registry", "Installed behavior-tree patterns and summaries.")}'
            f'{link_card("/wiki/schemas", "Schema explorer", "Inline and referenced blackboard schemas.")}'
            f'{link_card("/v1/docs", "REST API reference", "Machine-oriented endpoint cards and curl examples.")}'
            f'{link_card("/wiki/examples", "SSR examples", "How to add dashboards, wizard previews, and more.")}'
            "</div></section>"
            '<section class="section"><h2>Living documentation</h2>'
            "<p class=\"muted\">This wiki introspects the running Palm runtime — definitions, "
            "job context, snapshots, and registries update as your engine evolves. "
            "Use it for operator visibility and human-first exploration.</p></section>"
        )
        return html_response(
            wiki_page(
                title="Documentation Hub",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki",
                subtitle="Registry-driven documentation generated from your running Palm engine.",
            )
        )

    def flows(self, request: ServerRequest) -> ServerResponse:
        flows = self._fetch.list_flows()
        rows = [
            [
                f'<a href="/wiki/flows/{escape(flow.definition_id)}">{escape(flow.name)}</a>',
                escape(flow.pattern),
                "yes" if flow.has_state_schema else "—",
            ]
            for flow in flows
        ]
        content = (
            '<section class="section">'
            f"{data_table(['Name', 'Pattern', 'Schema'], rows) if rows else '<p class=\"muted\">No flows registered.</p>'}"
            "</section>"
        )
        return html_response(
            wiki_page(
                title="Flow Catalog",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/flows",
                subtitle="Registered flow definitions from the repository.",
            )
        )

    def flow_detail(self, request: ServerRequest, *, flow_id: str) -> ServerResponse:
        flow = self._fetch.get_flow(flow_id)
        if flow is None:
            return _not_found_page(self._fetch.version, f"Flow not found: {flow_id}")
        content = (
            '<section class="section"><div class="panel">'
            f"<p>{badge(flow.pattern)} {badge('schema' if flow.has_state_schema else 'no schema', tone='default')}</p>"
            f"{code_block(flow.to_dict())}"
            "</div></section>"
        )
        return html_response(
            wiki_page(
                title=flow.name,
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/flows",
                subtitle=f"Definition id: {flow.definition_id}",
            )
        )

    def processes(self, request: ServerRequest) -> ServerResponse:
        processes = self._fetch.list_processes()
        rows = [
            [
                f'<a href="/wiki/processes/{escape(proc.definition_id)}">{escape(proc.name)}</a>',
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
            wiki_page(
                title="Process Catalog",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/processes",
            )
        )

    def process_detail(self, request: ServerRequest, *, process_id: str) -> ServerResponse:
        process = self._fetch.get_process(process_id)
        if process is None:
            return _not_found_page(self._fetch.version, f"Process not found: {process_id}")
        content = f'<section class="section"><div class="panel">{code_block(process.to_dict())}</div></section>'
        return html_response(
            wiki_page(
                title=process.name,
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/processes",
            )
        )

    def patterns(self, request: ServerRequest) -> ServerResponse:
        patterns = self._fetch.list_patterns()
        rows = [
            [f"<code>{escape(item['name'])}</code>", escape(item["class"]), escape(item["summary"])]
            for item in patterns
        ]
        content = f'<section class="section">{data_table(["Pattern", "Class", "Summary"], rows)}</section>'
        return html_response(
            wiki_page(
                title="Pattern Registry",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/patterns",
                subtitle="Installed behavior-tree patterns from palm.patterns.",
            )
        )

    def schemas(self, request: ServerRequest) -> ServerResponse:
        schemas = self._fetch.list_schemas()
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
            wiki_page(
                title="Schema Explorer",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/schemas",
            )
        )

    def jobs(self, request: ServerRequest) -> ServerResponse:
        jobs = self._fetch.list_jobs(limit=50)
        rows = [
            [
                f'<a href="/wiki/jobs/{escape(row.get("job_id", ""))}">{escape(row.get("job_id", ""))}</a>',
                _status_badge(row.get("status", "")),
                escape(str(row.get("instance_id") or "—")),
            ]
            for row in jobs
        ]
        content = (
            '<section class="section">'
            f"{data_table(['Job', 'Status', 'Instance'], rows) if rows else '<p class=\"muted\">No jobs yet. Submit via POST /v1/jobs.</p>'}"
            "</section>"
        )
        return html_response(
            wiki_page(
                title="Jobs",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/jobs",
                subtitle="Click a job for the rich context viewer.",
            )
        )

    def job_detail(self, request: ServerRequest, *, job_id: str) -> ServerResponse:
        context = self._fetch.get_job_context(job_id)
        if not context.get("found", True):
            return _not_found_page(self._fetch.version, f"Job not found: {job_id}")

        instance = context.get("instance") or {}
        pattern = context.get("pattern") or {}
        prompt = pattern.get("prompt")
        content = (
            '<section class="section"><div class="grid-3">'
            f"{stat_card('Status', context.get('status', '—'))}"
            f"{stat_card('Pattern', pattern.get('pattern', '—'))}"
            f"{stat_card('Step', pattern.get('step') or '—')}"
            "</div></section>"
            '<section class="section"><div class="grid-2">'
            '<div class="panel"><h3>Interactive context</h3>'
            f"<p class=\"muted\">{escape(prompt) if prompt else 'No active prompt.'}</p>"
            f"{code_block(pattern)}"
            "</div>"
            '<div class="panel"><h3>Instance</h3>'
            f"<p><a href=\"{escape(instance.get('link', '#'))}\">{escape(instance.get('instance_id', '—'))}</a></p>"
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
            wiki_page(
                title=f"Job {job_id}",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/jobs",
                subtitle="Rich context assembled from live job state, projections, and snapshots.",
            )
        )

    def snapshots(self, request: ServerRequest, *, instance_id: str) -> ServerResponse:
        try:
            snapshots = self._fetch.list_snapshots(instance_id)
        except Exception:
            return _not_found_page(self._fetch.version, f"Instance not found: {instance_id}")

        rows = [
            [
                f'<a href="/wiki/instances/{escape(instance_id)}/snapshots/{index}">{index}</a>',
                escape(snap.status),
                escape(snap.recorded_at),
                escape(snap.wizard_step_slug or "—"),
            ]
            for index, snap in enumerate(snapshots)
        ]
        content = (
            f'<section class="section"><p><a href="/wiki/jobs">Jobs</a> · '
            f'<a href="/v1/instances/{escape(instance_id)}/snapshots">REST</a></p>'
            f"{data_table(['#', 'Status', 'Recorded', 'Step'], rows) if rows else '<p class=\"muted\">No snapshots captured.</p>'}"
            "</section>"
        )
        return html_response(
            wiki_page(
                title=f"Snapshots · {instance_id}",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/jobs",
            )
        )

    def snapshot_detail(
        self,
        request: ServerRequest,
        *,
        instance_id: str,
        snapshot_id: str,
    ) -> ServerResponse:
        resolved = self._fetch.get_snapshot(instance_id, snapshot_id)
        if resolved is None:
            return _not_found_page(self._fetch.version, f"Snapshot not found: {snapshot_id}")
        index, snapshot = resolved
        content = (
            f'<section class="section"><p><a href="/wiki/instances/{escape(instance_id)}/snapshots">← snapshots</a></p>'
            f'<div class="panel">{code_block({"snapshot_id": str(index), **snapshot.to_dict()})}</div>'
            "</section>"
        )
        return html_response(
            wiki_page(
                title=f"Snapshot {snapshot_id}",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/jobs",
            )
        )


def _status_badge(status: str) -> str:
    tone = "default"
    if status == "WAITING_FOR_INPUT":
        tone = "waiting"
    elif status == "SUCCEEDED":
        tone = "success"
    elif status in {"FAILED", "CANCELLED"}:
        tone = "error"
    return badge(status or "—", tone=tone)


def _not_found_page(version: str, message: str) -> ServerResponse:
    content = f'<section class="section"><p class="muted">{escape(message)}</p></section>'
    return html_response(
        wiki_page(title="Not found", version=version, content=content),
        status=404,
    )