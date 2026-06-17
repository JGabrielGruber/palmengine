"""Resource catalog, detail, and interactive invoke pages."""

from __future__ import annotations

import json
from typing import Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.ssr.explorer.components import (
    action_button,
    action_catalog,
    badge,
    code_block,
    data_table,
    definition_dl,
    empty_state,
    catalog_filter_form,
    link_pills,
    resource_timeline_table,
    stat_card,
)
from palm.runtimes.server.surfaces.ssr.explorer.forms import resource_invoke_form
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page
from palm.runtimes.server.surfaces.ssr.explorer.resource_helpers import (
    binding_preview,
    catalog_filters,
    definition_form_rows,
    describe_provider_actions,
    filter_catalog_entries,
    flows_using_resource,
    invocations_for_resource,
    invoke_href,
    provider_options,
    related_instances,
    related_jobs,
    resource_href,
    schema_label,
    usage_counts,
)
from palm.common.runtimes.server.ssr.render import escape, html_response
from .base import PageContext
from .utils import flash_banners, not_found_page


class ResourcePages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx

    def catalog(self, request: ServerRequest) -> ServerResponse:
        entries = self._ctx.fetch.list_resource_catalog()
        invocation_rows = self._ctx.fetch.list_resource_invocation_rows(limit=100)
        counts = usage_counts(invocation_rows)
        provider_filter, search_query = catalog_filters(request)
        filtered = filter_catalog_entries(
            entries,
            provider=provider_filter,
            query=search_query,
        )
        providers = provider_options(entries)

        rows = []
        for entry in filtered:
            schema = schema_label(entry.has_input_schema, entry.has_output_schema)
            usage = counts.get(entry.name, 0) + counts.get(entry.definition_id, 0)
            rows.append(
                [
                    f'<a href="{resource_href(entry.definition_id)}">{escape(entry.name)}</a>',
                    badge(entry.provider, tone="default"),
                    escape(entry.action),
                    badge(schema, tone="success" if schema != "—" else "default"),
                    escape(str(usage)),
                    (
                        f'<span class="btn-row">'
                        f'{action_button(invoke_href(entry.definition_id), "Invoke", tone="primary")}'
                        f"</span>"
                    ),
                ]
            )

        table_html = (
            data_table(
                ["Name", "Provider", "Action", "Schemas", "Usage", ""],
                rows,
            )
            if rows
            else empty_state(
                "No matching resources",
                "Register ResourceDefinition objects or adjust your filters.",
                action_href="/explorer/resources",
                action_label="Clear filters",
            )
        )

        filter_html = catalog_filter_form(
            action="/explorer/resources",
            providers=providers,
            selected_provider=provider_filter,
            query=search_query,
        )
        keyboard_script = (
            "<script>"
            "document.addEventListener('keydown',function(e){"
            "if(e.key==='/'&&document.querySelector('.filter-search')){"
            "e.preventDefault();document.querySelector('.filter-search').focus();}});"
            "</script>"
        )

        content = (
            '<section class="section">'
            f"{filter_html}"
            f'<p class="muted">{len(filtered)} of {len(entries)} resource(s)</p>'
            f"{table_html}"
            f"{keyboard_script}"
            "</section>"
        )
        return html_response(
            explorer_page(
                title="Resource Catalog",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/resources",
                subtitle="Declarative contracts for providers — invoke, compose, and observe.",
            )
        )

    def detail(self, request: ServerRequest, *, resource_id: str) -> ServerResponse:
        payload = self._ctx.fetch.describe_resource(resource_id)
        if payload is None:
            return not_found_page(self._ctx.version, f"Resource not found: {resource_id}")

        invocation_rows = self._ctx.fetch.list_resource_invocation_rows(limit=100)
        name = str(payload.get("name") or resource_id)
        definition_id = str(payload.get("definition_id") or resource_id)
        recent = invocations_for_resource(
            invocation_rows,
            name=name,
            definition_id=definition_id,
        )
        usage = len([e for e in recent if e.get("event_type") == "resource.completed"])
        flows = flows_using_resource(
            self._ctx.fetch.list_flows(),
            name=name,
            definition_id=definition_id,
        )
        actions = describe_provider_actions(payload)
        form_rows = definition_form_rows(payload)
        schema = schema_label(
            bool(payload.get("input_schema")),
            bool(payload.get("output_schema")),
        )

        flow_rows = [
            [
                f'<a href="/explorer/flows/{escape(item["flow_id"])}">{escape(item["flow_name"])}</a>',
                badge(str(item.get("pattern") or "flow"), tone="default"),
                escape(str(len(item.get("steps") or []))),
            ]
            for item in flows
        ]

        content = (
            f"{flash_banners(request)}"
            '<section class="section">'
            f'<p class="btn-row">'
            f'{action_button(invoke_href(definition_id), "Try Invoke", tone="primary")} '
            f'<a class="btn btn-default" href="/explorer/resources">← catalog</a>'
            f"</p>"
            "</section>"
            '<section class="section"><div class="grid-3">'
            f"{stat_card('Provider', payload.get('provider', '—'))}"
            f"{stat_card('Default action', payload.get('action', '—'))}"
            f"{stat_card('Completed invokes', usage)}"
            "</div></section>"
            '<section class="section"><div class="grid-2">'
            '<div class="panel">'
            "<h3>Definition</h3>"
            f"<p>{badge(payload.get('provider', ''), tone='default')} "
            f"{badge(schema, tone='success' if schema != '—' else 'default')}</p>"
            f"<p class=\"muted\">{escape(str(payload.get('provider_description') or ''))}</p>"
            f"{definition_dl(form_rows)}"
            '<details class="advanced-panel"><summary>Raw JSON</summary>'
            f"{code_block(payload)}"
            "</details>"
            "</div>"
            '<div class="panel">'
            "<h3>Action catalog</h3>"
            f"{action_catalog(actions)}"
            "</div>"
            "</div></section>"
            '<section class="section"><div class="grid-2">'
            '<div class="panel"><h3>Used by flows</h3>'
            f"{data_table(['Flow', 'Pattern', 'Steps'], flow_rows) if flow_rows else '<p class=\"muted\">Not referenced in any registered flow yet.</p>'}"
            "</div>"
            '<div class="panel"><h3>Related jobs &amp; instances</h3>'
            "<p><strong>Jobs</strong></p>"
            f"{link_pills(related_jobs(recent), key='job_id', label_key='job_id')}"
            "<p><strong>Instances</strong></p>"
            f"{link_pills(related_instances(recent), key='instance_id', label_key='instance_id')}"
            "</div>"
            "</div></section>"
            '<section class="section"><div class="panel">'
            "<h3>Recent invocations</h3>"
            f"{resource_timeline_table(recent)}"
            "</div></section>"
        )
        return html_response(
            explorer_page(
                title=name,
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/resources",
                subtitle=f"Definition id: {definition_id}",
            )
        )

    def invoke(self, request: ServerRequest, *, resource_id: str) -> ServerResponse:
        payload = self._ctx.fetch.describe_resource(resource_id)
        if payload is None:
            return not_found_page(self._ctx.version, f"Resource not found: {resource_id}")

        name = str(payload.get("name") or resource_id)
        definition_id = str(payload.get("definition_id") or resource_id)
        content = (
            f"{flash_banners(request)}"
            '<section class="section">'
            f'<p class="btn-row">'
            f'<a class="btn btn-default" href="{resource_href(definition_id)}">← {escape(name)}</a>'
            f"</p>"
            "</section>"
            '<section class="section"><div class="panel">'
            "<h3>Try Invoke</h3>"
            f'<p class="muted">Calls <code>{escape(name)}</code> via the runtime ResourceEngine. '
            f"Params support <code>{{{{ state.key }}}}</code> binding from the state JSON below.</p>"
            f"{resource_invoke_form(definition_id, payload)}"
            "</div></section>"
        )
        return html_response(
            explorer_page(
                title=f"Invoke · {name}",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/resources",
                subtitle="Interactive resource invocation with binding preview.",
            )
        )

    def invoke_post(self, request: ServerRequest, *, resource_id: str) -> ServerResponse:
        payload = self._ctx.fetch.describe_resource(resource_id)
        if payload is None:
            return not_found_page(self._ctx.version, f"Resource not found: {resource_id}")

        form = request.body or {}
        name = str(payload.get("name") or resource_id)
        definition_id = str(payload.get("definition_id") or resource_id)
        errors: list[str] = []
        state_json = str(form.get("state_json") or "{}").strip()
        state: dict[str, Any] = {}
        try:
            parsed = json.loads(state_json) if state_json else {}
            if not isinstance(parsed, dict):
                errors.append("state_json must be a JSON object")
            else:
                state = parsed
        except json.JSONDecodeError as exc:
            errors.append(f"state_json: {exc}")

        param_keys = payload.get("param_keys") or list((payload.get("params") or {}).keys())
        params: dict[str, Any] = {}
        for key in param_keys:
            raw = form.get(str(key))
            if raw is not None and str(raw).strip():
                params[str(key)] = str(raw).strip()

        action = str(form.get("action") or payload.get("action") or "fetch").strip()
        bound_resource_id = str(form.get("resource_id") or "").strip() or None
        binding_rows = binding_preview(dict(payload.get("params") or {}), state)

        result: Any | None = None
        if not errors:
            try:
                invoke_result = self._ctx.fetch.invoke_resource(
                    name,
                    action=action,
                    params=params,
                    state=state,
                    resource_id=bound_resource_id,
                )
                if invoke_result.success:
                    result = {
                        "success": True,
                        "data": invoke_result.data,
                        "metadata": invoke_result.metadata,
                    }
                else:
                    errors.append(invoke_result.error or "Invoke failed")
                    result = {
                        "success": False,
                        "error": invoke_result.error,
                        "metadata": invoke_result.metadata,
                    }
            except Exception as exc:
                errors.append(str(exc))

        form_values = {str(key): form.get(str(key), "") for key in param_keys}
        form_values["action"] = action
        form_values["resource_id"] = bound_resource_id or ""
        form_values["state_json"] = state_json

        content = (
            '<section class="section">'
            f'<p class="btn-row">'
            f'<a class="btn btn-default" href="{resource_href(definition_id)}">← {escape(name)}</a>'
            f"</p>"
            "</section>"
            '<section class="section"><div class="panel">'
            "<h3>Try Invoke</h3>"
            f"{resource_invoke_form(
                definition_id,
                payload,
                values=form_values,
                state_json=state_json,
                errors=errors or None,
                binding_rows=binding_rows,
                result=result,
            )}"
            "</div></section>"
        )
        return html_response(
            explorer_page(
                title=f"Invoke · {name}",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/resources",
                subtitle="Interactive resource invocation with binding preview.",
            )
        )