"""Serve Analytics dashboard dogfood static assets (0.35.6)."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from palm.common.runtimes.server.protocol import ServerResponse

_STATIC_ROOT = Path(__file__).resolve().parent / "static"


def analytics_static_root() -> Path:
    return _STATIC_ROOT


def analytics_file_response(relative: str) -> ServerResponse | None:
    root = _STATIC_ROOT.resolve()
    rel = relative.strip().lstrip("/") or "index.html"
    if not rel or ".." in rel.split("/") or rel.startswith("\\"):
        return None
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
    return ServerResponse(
        status=200,
        content_type=content_type,
        raw_body=candidate.read_bytes(),
        headers={"Cache-Control": "no-cache"},
    )


__all__ = ["analytics_file_response", "analytics_static_root"]
