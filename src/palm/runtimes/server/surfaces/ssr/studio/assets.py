"""Static asset resolution for the Palm Studio SPA."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path

from palm.common.runtimes.server.protocol import ServerResponse

_STATIC_ROOT = Path(__file__).resolve().parent / "static"


@dataclass(frozen=True)
class StaticAsset:
    """Resolved on-disk asset with inferred MIME type."""

    path: Path
    content_type: str


def static_root() -> Path:
    """Return the directory containing the Vite build output."""
    return _STATIC_ROOT


def resolve_asset(relative_path: str) -> StaticAsset | None:
    """
    Resolve a path relative to the static root.

    Rejects path traversal and returns ``None`` when the file is missing.
    """
    root = static_root().resolve()
    candidate = (root / relative_path).resolve()
    if not str(candidate).startswith(str(root)):
        return None
    if not candidate.is_file():
        return None
    content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
    return StaticAsset(path=candidate, content_type=content_type)


def file_response(asset: StaticAsset, *, status: int = 200) -> ServerResponse:
    """Return a binary response for a resolved static asset."""
    return ServerResponse(
        status=status,
        content_type=asset.content_type,
        raw_body=asset.path.read_bytes(),
    )


def index_asset() -> StaticAsset | None:
    """Return the SPA shell when the frontend has been built."""
    return resolve_asset("index.html")