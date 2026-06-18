"""Studio draft persistence — optional server-side draft storage."""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from typing import Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse

_store_lock = threading.RLock()
_drafts: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _draft_response(draft: dict[str, Any]) -> ServerResponse:
    return ServerResponse(status=200, body={"draft": draft})


def list_drafts(request: ServerRequest) -> ServerResponse:
    """List saved draft summaries."""
    with _store_lock:
        items = [
            {
                "id": draft["id"],
                "name": draft.get("name", "Untitled"),
                "updated_at": draft.get("updated_at"),
            }
            for draft in sorted(
                _drafts.values(),
                key=lambda row: row.get("updated_at", ""),
                reverse=True,
            )
        ]
    return ServerResponse(status=200, body={"drafts": items})


def get_draft(request: ServerRequest, *, draft_id: str) -> ServerResponse:
    """Return a single draft by id."""
    with _store_lock:
        draft = _drafts.get(draft_id)
    if draft is None:
        return ServerResponse(
            status=404,
            body={"error": "not_found", "message": f"Draft {draft_id!r} not found"},
        )
    return _draft_response(draft)


def save_draft(request: ServerRequest) -> ServerResponse:
    """Create or update a draft from JSON body."""
    body = request.body
    if not isinstance(body, dict):
        return ServerResponse(
            status=400,
            body={"error": "invalid_request", "message": "JSON object body required"},
        )

    canvas = body.get("canvas")
    if not isinstance(canvas, dict):
        return ServerResponse(
            status=400,
            body={"error": "invalid_request", "message": "canvas object required"},
        )

    draft_id = str(body.get("id") or uuid.uuid4())
    timestamp = _now_iso()
    draft: dict[str, Any] = {
        "id": draft_id,
        "name": str(body.get("name") or "Untitled"),
        "pattern": str(body.get("pattern") or "wizard"),
        "canvas": canvas,
        "updated_at": timestamp,
    }
    if "created_at" in body:
        draft["created_at"] = body["created_at"]
    else:
        with _store_lock:
            existing = _drafts.get(draft_id)
        draft["created_at"] = existing.get("updated_at", timestamp) if existing else timestamp

    with _store_lock:
        _drafts[draft_id] = draft

    return ServerResponse(status=200, body={"draft": draft})


def clear_drafts() -> None:
    """Reset draft storage (testing helper)."""
    with _store_lock:
        _drafts.clear()