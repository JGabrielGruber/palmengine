"""REST request validation — query coercion and pagination."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.schema_validation import validate_query_dict
from palm.runtimes.server.surfaces.rest.schemas import (
    LIST_FLOWS_QUERY,
    LIST_INSTANCES_QUERY,
    LIST_JOBS_QUERY,
    LIST_SNAPSHOTS_QUERY,
)

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


@dataclass(frozen=True)
class PaginationParams:
    limit: int
    offset: int


def parse_list_jobs_query(request: ServerRequest) -> dict[str, Any] | ServerResponse:
    """Coerce and validate job list query parameters."""
    coerced = _coerce_pagination_query(request.query)
    if isinstance(coerced, ServerResponse):
        return coerced
    status = request.query.get("status")
    if status is not None:
        coerced["status"] = status
    return validate_query_dict(coerced, LIST_JOBS_QUERY)


def parse_list_instances_query(request: ServerRequest) -> dict[str, Any] | ServerResponse:
    """Coerce and validate instance list query parameters."""
    coerced = _coerce_pagination_query(request.query)
    if isinstance(coerced, ServerResponse):
        return coerced

    status = request.query.get("status")
    if status is not None:
        coerced["status"] = status
    flow_name = request.query.get("flow_name")
    if flow_name is not None:
        coerced["flow_name"] = flow_name

    include_raw = request.query.get("include_terminal")
    if include_raw is not None:
        coerced["include_terminal"] = include_raw.lower() not in {"false", "0", "no"}

    validated = validate_query_dict(coerced, LIST_INSTANCES_QUERY)
    if isinstance(validated, ServerResponse):
        return validated
    if "include_terminal" not in validated:
        validated["include_terminal"] = True
    return validated


def parse_list_flows_query(request: ServerRequest) -> dict[str, Any] | ServerResponse:
    """Coerce and validate flow/process catalog list query parameters."""
    coerced = _coerce_pagination_query(request.query)
    if isinstance(coerced, ServerResponse):
        return coerced
    pattern = request.query.get("pattern")
    if pattern is not None:
        coerced["pattern"] = pattern
    return validate_query_dict(coerced, LIST_FLOWS_QUERY)


def parse_list_snapshots_query(request: ServerRequest) -> dict[str, Any] | ServerResponse:
    """Coerce and validate snapshot list query parameters."""
    coerced = _coerce_pagination_query(request.query)
    if isinstance(coerced, ServerResponse):
        return coerced
    return validate_query_dict(coerced, LIST_SNAPSHOTS_QUERY)


def _coerce_pagination_query(query: dict[str, str]) -> dict[str, Any] | ServerResponse:
    limit_raw = query.get("limit")
    offset_raw = query.get("offset", "0")

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
        return {"limit": DEFAULT_LIMIT, "offset": offset}

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

    return {"limit": limit, "offset": offset}