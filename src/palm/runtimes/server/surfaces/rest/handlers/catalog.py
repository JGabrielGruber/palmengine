"""Catalog endpoints — registered flow and process definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.pagination import list_envelope
from palm.runtimes.server.surfaces.rest.responses import ok
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.schemas import VALIDATE_FLOW_BODY
from palm.runtimes.server.surfaces.rest.validation import PaginationParams, parse_list_flows_query

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def validate_flow(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    from palm.runtimes.server.surfaces.rest.schemas import validate_flow_variant_errors

    body = validate_body(
        request,
        VALIDATE_FLOW_BODY,
        extra_errors=validate_flow_variant_errors(request.body or {}),
    )
    if isinstance(body, ServerResponse):
        return body

    try:
        result = ctx.definition.validate_flow(body, runtime=ctx.runtime)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.validation_failed(
            [{"field": "flow", "message": str(exc), "code": "build_failed"}]
        )

    return ok(result)


def list_flows(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    query = parse_list_flows_query(request)
    if isinstance(query, ServerResponse):
        return query

    rows = ctx.definition.list_flows(pattern=query.get("pattern"))
    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("flows", rows, params))


def get_flow(ctx: ServerContext, request: ServerRequest, *, flow_id: str) -> ServerResponse:
    try:
        payload = ctx.definition.get_flow(flow_id, verbose=_verbose_query(request))
    except DefinitionNotFoundServiceError:
        return errors.flow_not_found(flow_id)
    return ok(payload)


def _verbose_query(request: ServerRequest) -> bool:
    raw = request.query.get("verbose")
    if raw is None:
        return True
    return str(raw).strip().lower() not in {"0", "false", "no"}


def list_processes(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    query = parse_list_flows_query(request)
    if isinstance(query, ServerResponse):
        return query

    rows = ctx.definition.list_processes()
    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("processes", rows, params))


def get_process(ctx: ServerContext, request: ServerRequest, *, process_id: str) -> ServerResponse:
    try:
        payload = ctx.definition.get_process(process_id)
    except DefinitionNotFoundServiceError:
        return errors.process_not_found(process_id)
    return ok(payload)
