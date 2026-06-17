"""
Shared response helpers — consistent error envelopes for all surfaces.
"""

from __future__ import annotations

from typing import Any

from palm.common.runtimes.server.protocol import ServerResponse


def error_response(
    status: int,
    code: str,
    message: str,
    *,
    details: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> ServerResponse:
    """
    Build an OpenAPI-friendly error payload.

    Keeps top-level ``error`` for backward compatibility; ``message`` and
    ``detail`` carry the human-readable text.
    """
    body: dict[str, Any] = {
        "error": code,
        "message": message,
        "detail": message,
    }
    if details:
        body["details"] = details
    if extra:
        body.update(extra)
    return ServerResponse(status=status, body=body)


def not_found(path: str) -> ServerResponse:
    return error_response(404, "not_found", f"Route not found: {path}", extra={"path": path})


def unauthorized(message: str) -> ServerResponse:
    return error_response(401, "unauthorized", message)
