"""Instance browser and snapshot pages."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.render import escape, html_response
from palm.runtimes.server.surfaces.ssr.explorer.components import (
    action_button,
    badge,
    code_block,
    data_table,
    stat_card,
)
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page

from .base import PageContext
from .utils import not_found_page, status_badge
from .wizards import WizardPages


class InstancePages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx
        self._wizards = WizardPages(ctx)

    def _resource_timeline(
        self,
        *,
        instance_id: str,
        job_id: str | None,
    ) -> str:
        payload = self._ctx.fetch.get_resource_invocations(
            instance_id=instance_id,
            job_id=job_id,
        )
        if not payload:
            return (
                '<section class="section"><h2>Resource timeline</h2>'
                '<p class="muted">No resource invocations recorded yet.</p></section>'
            )
        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            return (
                '<section class="section"><h2>Resource timeline</h2>'
                '<p class="muted">No resource invocations recorded yet.</p></section>'
            )
        rows = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            status = (
                "ok" if entry.get("success") else ("fail" if entry.get("success") is False else "—")
            )
            rows.append(
                [
                    escape(str(entry.get("recorded_at") or "—")),
                    escape(str(entry.get("event_type") or "—")),
                    escape(str(entry.get("resource_ref") or entry.get("definition_name") or "—")),
                    escape(str(entry.get("action") or "—")),
                    escape(str(entry.get("step_slug") or "—")),
                    escape(status),
                ]
            )
        table = data_table(
            ["Recorded", "Event", "Resource", "Action", "Step", "Status"],
            rows,
        )
        return f'<section class="section"><h2>Resource timeline</h2>{table}</section>'

    def catalog(self, request: ServerRequest) -> ServerResponse:
        instances = self._ctx.fetch.list_instances(limit=50)
        flow_patterns = self._ctx.fetch.flow_pattern_by_name()
        rows = []
        for row in instances:
            instance_id = str(row.get("instance_id") or "")
            flow_name = str(row.get("flow_name") or "")
            is_wizard = flow_patterns.get(flow_name) == "wizard" or bool(
                row.get("current_step_slug")
            )
            if not is_wizard and row.get("status") == "WAITING_FOR_INPUT":
                wizard_view = self._ctx.fetch.get_wizard(instance_id)
                is_wizard = bool(wizard_view and wizard_view.get("pattern") == "wizard")
            pattern_cell = badge("Wizard", tone="waiting") if is_wizard else "—"
            continue_cell = "—"
            if is_wizard and row.get("status") == "WAITING_FOR_INPUT":
                continue_cell = action_button(
                    f"/explorer/instances/{instance_id}",
                    "Continue",
                    tone="primary",
                )
            rows.append(
                [
                    f'<a href="/explorer/instances/{escape(instance_id)}">{escape(instance_id)}</a>',
                    status_badge(str(row.get("status") or "—")),
                    escape(flow_name or "—"),
                    pattern_cell,
                    escape(str(row.get("current_step_slug") or "—")),
                    continue_cell,
                ]
            )
        content = (
            '<section class="section">'
            f"{data_table(['Instance', 'Status', 'Flow', 'Pattern', 'Step', ''], rows) if rows else '<p class=\"muted\">No instances yet.</p>'}"
            "</section>"
        )
        return html_response(
            explorer_page(
                title="Instance Browser",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/instances",
                subtitle="Durable process instances with links to snapshots and jobs.",
            )
        )

    def detail(self, request: ServerRequest, *, instance_id: str) -> ServerResponse:
        instance = self._ctx.fetch.get_instance(instance_id)
        if instance is None:
            return not_found_page(self._ctx.version, f"Instance not found: {instance_id}")

        if self._wizards.is_wizard_instance(instance_id, instance):
            return self._wizards.detail(request, instance_id=instance_id, instance=instance)

        job_id = instance.get("job_id", "")
        timeline = self._resource_timeline(instance_id=instance_id, job_id=job_id or None)
        content = (
            '<section class="section"><div class="grid-2">'
            f"{stat_card('Status', instance.get('status', '—'))}"
            f"{stat_card('Flow', instance.get('flow_name') or '—')}"
            "</div></section>"
            f"{timeline}"
            '<section class="section"><div class="panel">'
            f'<p><a href="/explorer/instances/{escape(instance_id)}/snapshots">View snapshots</a>'
            f'{f" · <a href=\"/explorer/jobs/{escape(job_id)}\">View job</a>" if job_id else ""}'
            f' · <a href="/v1/api/system/instances/{escape(instance_id)}">REST</a></p>'
            f"{code_block(instance)}"
            "</div></section>"
        )
        return html_response(
            explorer_page(
                title=f"Instance {instance_id}",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/instances",
            )
        )

    def snapshots(self, request: ServerRequest, *, instance_id: str) -> ServerResponse:
        try:
            snapshots = self._ctx.fetch.list_snapshots(instance_id)
        except Exception:
            return not_found_page(self._ctx.version, f"Instance not found: {instance_id}")

        rows = [
            [
                f'<a href="/explorer/instances/{escape(instance_id)}/snapshots/{index}">{index}</a>',
                escape(snap.status),
                escape(snap.recorded_at),
                escape(snap.current_step_slug or "—"),
            ]
            for index, snap in enumerate(snapshots)
        ]
        content = (
            f'<section class="section"><p>'
            f'<a href="/explorer/instances/{escape(instance_id)}">← instance</a> · '
            f'<a href="/explorer/jobs">Jobs</a> · '
            f'<a href="/v1/api/system/instances/{escape(instance_id)}/snapshots">REST</a></p>'
            f"{data_table(['#', 'Status', 'Recorded', 'Step'], rows) if rows else '<p class=\"muted\">No snapshots captured.</p>'}"
            "</section>"
        )
        return html_response(
            explorer_page(
                title=f"Snapshots · {instance_id}",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/instances",
            )
        )

    def snapshot_detail(
        self,
        request: ServerRequest,
        *,
        instance_id: str,
        snapshot_id: str,
    ) -> ServerResponse:
        resolved = self._ctx.fetch.get_snapshot(instance_id, snapshot_id)
        if resolved is None:
            return not_found_page(self._ctx.version, f"Snapshot not found: {snapshot_id}")
        index, snapshot = resolved
        content = (
            f'<section class="section"><p><a href="/explorer/instances/{escape(instance_id)}/snapshots">← snapshots</a></p>'
            f'<div class="panel">{code_block({"snapshot_id": str(index), **snapshot.to_dict()})}</div>'
            "</section>"
        )
        return html_response(
            explorer_page(
                title=f"Snapshot {snapshot_id}",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/instances",
            )
        )
