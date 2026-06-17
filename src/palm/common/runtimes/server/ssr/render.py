"""SSR rendering primitives — HTML responses without external template engines."""

from __future__ import annotations

import html
import json
from typing import Any

from palm.common.runtimes.server.protocol import ServerResponse


def escape(text: object | None) -> str:
    """Escape text for safe HTML embedding."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def html_response(body: str, *, status: int = 200) -> ServerResponse:
    """Return a UTF-8 HTML response."""
    return ServerResponse(
        status=status,
        content_type="text/html; charset=utf-8",
        raw_body=body.encode("utf-8"),
    )


def redirect(location: str, *, status: int = 302) -> ServerResponse:
    """Issue an HTTP redirect."""
    return ServerResponse(
        status=status,
        headers={"Location": location},
        content_type="text/html; charset=utf-8",
        raw_body=b"",
    )


def pretty_json(value: Any) -> str:
    """Format JSON for display inside ``<pre>`` blocks."""
    return escape(json.dumps(value, indent=2, default=str))