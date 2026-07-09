"""Serve Palm Portal static dogfood assets (0.32.4)."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from palm.common.runtimes.server.protocol import ServerResponse

_STATIC_ROOT = Path(__file__).resolve().parent / "static"


def portal_static_root() -> Path:
    return _STATIC_ROOT


def portal_file_response(relative: str) -> ServerResponse | None:
    """Return a static file under portal static root, or None if missing/unsafe."""
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
    if candidate.suffix == ".webmanifest":
        content_type = "application/manifest+json"
    return ServerResponse(
        status=200,
        content_type=content_type,
        raw_body=candidate.read_bytes(),
        headers={"Cache-Control": "no-cache"},
    )


__all__ = ["portal_file_response", "portal_static_root"]
