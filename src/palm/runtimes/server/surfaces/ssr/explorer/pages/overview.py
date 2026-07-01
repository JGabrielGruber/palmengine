"""Explorer home overview page."""

from __future__ import annotations

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.render import html_response
from palm.runtimes.server.surfaces.ssr.explorer.components import link_card, stat_card
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page

from .base import PageContext


class OverviewPages:
    def __init__(self, ctx: PageContext) -> None:
        self._ctx = ctx

    def overview(self, request: ServerRequest) -> ServerResponse:
        flows = self._ctx.fetch.list_flows()
        processes = self._ctx.fetch.list_processes()
        patterns = self._ctx.fetch.list_patterns()
        resources = self._ctx.fetch.list_resource_catalog()
        jobs = self._ctx.fetch.list_jobs(limit=20)
        instances = self._ctx.fetch.list_instances(limit=20)
        content = (
            '<section class="section"><div class="grid-3">'
            f"{stat_card('Flows', len(flows), hint='Registered definitions')}"
            f"{stat_card('Processes', len(processes), hint='Multi-flow bundles')}"
            f"{stat_card('Resources', len(resources), hint='Declarative resource contracts')}"
            f"{stat_card('Patterns', len(patterns), hint='Installed BT patterns')}"
            f"{stat_card('Jobs', len(jobs), hint='Live orchestration')}"
            f"{stat_card('Instances', len(instances), hint='Durable process state')}"
            "</div></section>"
            '<section class="section"><h2>Explore</h2><div class="grid-2">'
            f'{link_card("/explorer/assist", "Assist", "Guided operator entry with assistant-shaped turns.")}'
            f'{link_card("/explorer/flows", "Flow catalog", "Browse wizard, DAG, and pipeline definitions.")}'
            f'{link_card("/explorer/resources", "Resource catalog", "Declarative contracts, invoke, and timelines.")}'
            f'{link_card("/explorer/flows/submit", "Submit flow", "Start a job with a schema-driven form.")}'
            f'{link_card("/explorer/jobs", "Job context viewer", "Rich interactive state with input forms.")}'
            f'{link_card("/explorer/instances", "Instance browser", "Durable instances, snapshots, and resume.")}'
            f'{link_card("/explorer/patterns", "Pattern registry", "Installed behavior-tree patterns and summaries.")}'
            f'{link_card("/explorer/schemas", "Schema explorer", "Inline and referenced blackboard schemas.")}'
            f'{link_card("/v1/docs", "REST API reference", "Machine-oriented endpoint cards and curl examples.")}'
            f'{link_card("/explorer/examples", "SSR examples", "How to add dashboards, wizard previews, and more.")}'
            "</div></section>"
            '<section class="section"><h2>Living introspection</h2>'
            "<p class=\"muted\">Palm Explorer introspects the running engine — definitions, "
            "job context, snapshots, and registries update as your flows evolve. "
            "Use it for operator visibility and human-first control.</p></section>"
        )
        return html_response(
            explorer_page(
                title="Introspection Hub",
                version=self._ctx.version,
                content=content,
                active_nav="/explorer",
                subtitle="Registry-driven views and forms generated from your running Palm engine.",
            )
        )
