"""Wizard instance detail — interactive Explorer view."""

from __future__ import annotations

from typing import Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.render import escape, html_response
from palm.runtimes.server.surfaces.ssr.explorer.components import wizard_workspace
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page

from .base import PageContext
from .utils import flash_banners, is_htmx_request, not_found_page, query_message


class WizardPages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx

    def is_wizard_instance(self, instance_id: str, instance: dict[str, Any]) -> bool:
        wizard = self._ctx.fetch.get_wizard(instance_id)
        if wizard and wizard.get("pattern") == "wizard":
            return True
        if wizard and (wizard.get("prompt") or wizard.get("wizard_progress")):
            return True

        job_id = instance.get("job_id")
        if job_id:
            job_ctx = self._ctx.fetch.get_job_context(str(job_id))
            pattern = job_ctx.get("pattern") or {}
            if pattern.get("pattern") == "wizard":
                return True

        flow_name = instance.get("flow_name")
        if flow_name:
            patterns = self._ctx.fetch.flow_pattern_by_name()
            if patterns.get(str(flow_name)) == "wizard":
                return True

        return bool(instance.get("wizard_step_slug"))

    def detail(
        self,
        request: ServerRequest,
        *,
        instance_id: str,
        instance: dict[str, Any],
        notice: str = "",
        error: str = "",
    ) -> ServerResponse:
        wizard = self._ctx.fetch.get_wizard(instance_id)
        if wizard is None:
            return not_found_page(self._ctx.version, f"Wizard not found: {instance_id}")

        notice = notice or query_message(request, "notice")
        error = error or query_message(request, "error")
        htmx = is_htmx_request(request)
        workspace = wizard_workspace(
            instance_id,
            wizard,
            notice=notice if htmx else "",
            error=error if htmx else "",
            total_steps=_estimate_step_total(self._ctx.fetch, wizard, instance),
        )

        if htmx:
            return html_response(workspace)

        content = (
            f"{flash_banners(request)}"
            f"{workspace}"
            '<section class="section muted">'
            f'<p>Instance <code>{escape(instance_id)}</code> · '
            f'<a href="/v1/wizards/{escape(instance_id)}">API</a></p>'
            "</section>"
        )
        flow_name = wizard.get("flow_name") or "Wizard"
        return html_response(
            explorer_page(
                title=f"Wizard · {flow_name}",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer/instances",
                subtitle=f"Interactive wizard for instance {instance_id}",
            )
        )


def _estimate_step_total(fetch: Any, wizard: dict[str, Any], instance: dict[str, Any]) -> int:
    progress = wizard.get("wizard_progress") or {}
    completed = progress.get("completed_steps") or []
    current = progress.get("current_step") or wizard.get("wizard_step_slug")
    baseline = len(completed) + (1 if current else 0)

    flow_name = instance.get("flow_name") or wizard.get("flow_name")
    if flow_name:
        flow = fetch.get_flow(str(flow_name))
        if flow is not None:
            steps = (flow.options or {}).get("steps")
            if isinstance(steps, list):
                return max(len(steps), baseline)
            if isinstance(steps, int):
                return max(steps, baseline)
    return max(baseline, 1)