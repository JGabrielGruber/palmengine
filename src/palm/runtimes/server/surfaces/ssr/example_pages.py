"""
SSR example pages — templates for future dashboards and wizard previews.

Add a new page by:
1. Implementing a handler on :class:`~palm.runtimes.server.surfaces.ssr.wiki.pages.WikiPages`
   or a dedicated class in this module.
2. Registering the route in :mod:`palm.runtimes.server.surfaces.ssr.routes`.
3. Adding a nav link in :mod:`palm.common.runtimes.server.ssr.layout` when the page is stable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.components import code_block, link_card
from palm.common.runtimes.server.ssr.fetch import SsrFetcher
from palm.common.runtimes.server.ssr.layout import wiki_page
from palm.common.runtimes.server.ssr.render import html_response

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


class ExamplePages:
    """Illustrative SSR routes showing how to extend the wiki surface."""

    def __init__(self, ctx: ServerContext) -> None:
        self._fetch = SsrFetcher(ctx)

    def index(self, request: ServerRequest) -> ServerResponse:
        content = (
            '<section class="section"><h2>Adding SSR pages</h2>'
            "<p class=\"muted\">SSR pages compose HTML from "
            "<code>SsrFetcher</code> (CQRS), <code>components</code>, and "
            "<code>wiki_page</code> layout. No external template engine required.</p>"
            f"{code_block(_EXTENSION_STEPS)}"
            "</section>"
            '<section class="section"><h2>Future surfaces</h2><div class="grid-2">'
            f'{link_card("/wiki/examples/wizard-preview", "Wizard preview stub", "Placeholder for step-by-step wizard UI.")}'
            f'{link_card("/wiki/examples/dashboard", "Dashboard stub", "Placeholder for live job board HTML.")}'
            "</div></section>"
        )
        return html_response(
            wiki_page(
                title="SSR Examples",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/examples",
                subtitle="Patterns for dashboards, wizard previews, and operator tooling.",
            )
        )

    def wizard_preview(self, request: ServerRequest) -> ServerResponse:
        """Stub — replace with a rendered wizard step using job context + forms."""
        content = (
            '<section class="section"><div class="panel">'
            "<h3>Wizard preview (stub)</h3>"
            "<p class=\"muted\">A future implementation would render the active prompt, "
            "choices, and validation from <code>GetJobContextQuery</code>, posting input "
            "to <code>POST /v1/jobs/{id}/input</code>.</p>"
            f"{code_block({'next': 'wiki/jobs/{{job_id}}', 'data_source': '/v1/jobs/{{job_id}}/context'})}"
            "</div></section>"
        )
        return html_response(
            wiki_page(
                title="Wizard Preview",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/examples",
            )
        )

    def dashboard(self, request: ServerRequest) -> ServerResponse:
        """Stub — replace with charts/tables from projections."""
        jobs = self._fetch.list_jobs(limit=10)
        content = (
            '<section class="section"><div class="panel">'
            "<h3>Live dashboard (stub)</h3>"
            "<p class=\"muted\">Projections like <code>JobStatusBoard</code> and "
            "<code>WizardProgress</code> can feed real-time HTML tables here.</p>"
            f"{code_block(jobs)}"
            "</div></section>"
        )
        return html_response(
            wiki_page(
                title="Dashboard",
                version=self._fetch.version,
                content=content,
                active_nav="/wiki/examples",
            )
        )


_EXTENSION_STEPS = {
    "1": "Create a handler returning html_response(wiki_page(...))",
    "2": "Use SsrFetcher to call existing CQRS queries",
    "3": "Register GET route in surfaces/ssr/routes.py",
    "4": "Add tests in tests/test_server_ssr.py",
}