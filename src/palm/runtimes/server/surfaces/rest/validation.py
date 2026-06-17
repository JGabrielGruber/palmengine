"""REST request validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest import errors

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


@dataclass(frozen=True)
class PaginationParams:
    limit: int
    offset: int


def require_body(request: ServerRequest) -> dict[str, Any] | ServerResponse:
    if request.body is None:
        return errors.empty_body()
    return request.body


def require_fields(
    body: dict[str, Any],
    *fields: str,
) -> list[dict[str, str]] | None:
    """Return field error details when required keys are missing."""
    missing = [field for field in fields if field not in body]
    if not missing:
        return None
    return [{"field": field, "message": f"'{field}' is required"} for field in missing]


def parse_pagination(request: ServerRequest) -> PaginationParams | ServerResponse:
    limit_raw = request.query.get("limit")
    offset_raw = request.query.get("offset", "0")

    try:
        offset = int(offset_raw)
    except ValueError:
        return errors.bad_request(
            "offset must be an integer",
            details=[{"field": "offset", "message": "must be an integer"}],
        )

    if offset < 0:
        return errors.bad_request(
            "offset must be >= 0",
            details=[{"field": "offset", "message": "must be >= 0"}],
        )

    if limit_raw is None:
        return PaginationParams(limit=DEFAULT_LIMIT, offset=offset)

    try:
        limit = int(limit_raw)
    except ValueError:
        return errors.bad_request(
            "limit must be an integer",
            details=[{"field": "limit", "message": "must be an integer"}],
        )

    if limit < 1:
        return errors.bad_request(
            "limit must be >= 1",
            details=[{"field": "limit", "message": "must be >= 1"}],
        )
    if limit > MAX_LIMIT:
        return errors.bad_request(
            f"limit must be <= {MAX_LIMIT}",
            details=[{"field": "limit", "message": f"maximum is {MAX_LIMIT}"}],
        )

    return PaginationParams(limit=limit, offset=offset)


def parse_optional_int(
    value: str | None,
    *,
    field: str,
) -> int | None | ServerResponse:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return errors.bad_request(
            f"{field} must be an integer",
            details=[{"field": field, "message": "must be an integer"}],
        )


def validate_plan_ids(body: dict[str, Any]) -> list[str] | ServerResponse:
    plan_ids = body.get("plan_ids")
    if not isinstance(plan_ids, list) or not plan_ids:
        return errors.bad_request(
            "plan_ids must be a non-empty list",
            details=[{"field": "plan_ids", "message": "must be a non-empty list"}],
        )
    return [str(plan_id) for plan_id in plan_ids]