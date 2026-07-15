"""Shared surface pagination — list envelopes and pagination params.

Transport-agnostic (see :mod:`palm.common.surfaces`). Used by REST, MCP, SSR and
WebSocket surfaces alike. Relocated from the REST surface in 0.47.3.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


@dataclass(frozen=True)
class PaginationParams:
    limit: int
    offset: int


def paginate_rows(rows: list[Any], params: PaginationParams) -> dict[str, Any]:
    """Slice ``rows`` and return a list envelope with pagination metadata."""
    total = len(rows)
    start = params.offset
    end = start + params.limit
    page = rows[start:end]
    return {
        "items": page,
        "pagination": {
            "limit": params.limit,
            "offset": params.offset,
            "count": len(page),
            "total": total,
            "has_more": end < total,
        },
    }


def list_envelope(key: str, rows: list[Any], params: PaginationParams) -> dict[str, Any]:
    """Backward-compatible list key plus pagination block."""
    sliced = paginate_rows(rows, params)
    return {
        key: sliced["items"],
        "pagination": sliced["pagination"],
    }
