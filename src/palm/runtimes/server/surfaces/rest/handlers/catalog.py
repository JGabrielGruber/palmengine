"""Catalog endpoints — registered flow and process definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.cqrs.query import GetFlowQuery, GetProcessQuery, ListFlowsQuery, ListProcessesQuery
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.pagination import list_envelope
from palm.runtimes.server.surfaces.rest.responses import ok
from palm.runtimes.server.surfaces.rest.serializers import (
    flow_detail,
    flow_summary,
    process_detail,
    process_summary,
)
from palm.common.runtimes.server.plans import prepare_flow_from_body
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.schemas import VALIDATE_FLOW_BODY
from palm.runtimes.server.surfaces.rest.serializers import flow_step_slugs
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
        plan = prepare_flow_from_body(ctx.runtime, body)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.validation_failed(
            [{"field": "flow", "message": str(exc), "code": "build_failed"}]
        )

    pattern = plan.metadata.get("pattern") or body.get("flow", {}).get("pattern")
    flow_name = plan.metadata.get("flow") or plan.metadata.get("flow_name")
    step_slugs: list[str] = []
    flow_def = plan.metadata.get("flow_definition")
    if isinstance(flow_def, dict):
        from palm.definitions.flow import FlowDefinition

        step_slugs = flow_step_slugs(FlowDefinition.from_dict(flow_def))

    return ok(
        {
            "valid": True,
            "pattern": pattern,
            "flow": flow_name,
            "step_slugs": step_slugs,
        }
    )


def list_flows(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    query = parse_list_flows_query(request)
    if isinstance(query, ServerResponse):
        return query

    flows = ctx.ask(ListFlowsQuery(pattern=query.get("pattern")))
    rows = [flow_summary(flow) for flow in flows]
    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("flows", rows, params))


def get_flow(ctx: ServerContext, request: ServerRequest, *, flow_id: str) -> ServerResponse:
    flow = ctx.ask(GetFlowQuery(flow_id=flow_id))
    if flow is None:
        return errors.flow_not_found(flow_id)
    if _verbose_query(request):
        return ok(flow_detail(flow))
    return ok(flow_summary(flow))


def _verbose_query(request: ServerRequest) -> bool:
    raw = request.query.get("verbose")
    if raw is None:
        return True
    return str(raw).strip().lower() not in {"0", "false", "no"}


def list_processes(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    query = parse_list_flows_query(request)
    if isinstance(query, ServerResponse):
        return query

    processes = ctx.ask(ListProcessesQuery())
    rows = [process_summary(process) for process in processes]
    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("processes", rows, params))


def get_process(ctx: ServerContext, request: ServerRequest, *, process_id: str) -> ServerResponse:
    process = ctx.ask(GetProcessQuery(process_id=process_id))
    if process is None:
        return errors.process_not_found(process_id)
    return ok(process_detail(process))
