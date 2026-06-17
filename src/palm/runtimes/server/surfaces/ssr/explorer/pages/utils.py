"""Shared helpers for Explorer page modules."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.render import escape, html_response
from palm.runtimes.server.surfaces.ssr.explorer.components import badge
from palm.runtimes.server.surfaces.ssr.explorer.layout import explorer_page

if TYPE_CHECKING:
    from palm.definitions.flow import FlowDefinition


def flow_description(flow: FlowDefinition) -> str:
    """Human-readable summary for catalog and submit forms."""
    options = flow.options or {}
    explicit = options.get("description")
    if explicit:
        return str(explicit)

    if flow.pattern == "wizard":
        steps = options.get("steps", [])
        if isinstance(steps, list) and steps:
            return f"Wizard with {len(steps)} step(s)"
        return "Wizard flow"

    return f"{flow.pattern} pattern"


def flow_option_label(flow: FlowDefinition) -> str:
    """Rich dropdown label: name · pattern · description."""
    return f"{flow.name} · {flow.pattern} · {flow_description(flow)}"


def start_flow_href(flow_id: str) -> str:
    """Link to the submit form with a pre-selected flow."""
    return f"/explorer/flows/submit?flow={quote(flow_id, safe='')}"


def status_badge(status: str) -> str:
    tone = "default"
    if status == "WAITING_FOR_INPUT":
        tone = "waiting"
    elif status == "SUCCEEDED":
        tone = "success"
    elif status in {"FAILED", "CANCELLED"}:
        tone = "error"
    return badge(status or "—", tone=tone)


def query_message(request: ServerRequest, key: str) -> str:
    from urllib.parse import unquote

    raw = request.query.get(key)
    return unquote(raw) if raw else ""


def query_flow_id(request: ServerRequest) -> str:
    return query_message(request, "flow")


def not_found_page(version: str, message: str) -> ServerResponse:
    content = f'<section class="section"><p class="muted">{escape(message)}</p></section>'
    return html_response(
        explorer_page(title="Not found", version=version, content=content),
        status=404,
    )


def flash_banners(request: ServerRequest) -> str:
    from palm.runtimes.server.surfaces.ssr.explorer.forms import alert

    notice = query_message(request, "notice")
    error = query_message(request, "error")
    banners = ""
    if notice:
        banners += alert(notice)
    if error:
        banners += alert(error, tone="error")
    return banners
