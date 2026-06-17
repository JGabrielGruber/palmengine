"""REST pagination envelopes."""

from __future__ import annotations

from typing import Any

from palm.runtimes.server.surfaces.rest.validation import PaginationParams


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


def list_envelope(
    key: str,
    rows: list[Any],
    params: PaginationParams,
) -> dict[str, Any]:
    """Backward-compatible list key plus pagination block."""
    sliced = paginate_rows(rows, params)
    return {
        key: sliced["items"],
        "pagination": sliced["pagination"],
    }
