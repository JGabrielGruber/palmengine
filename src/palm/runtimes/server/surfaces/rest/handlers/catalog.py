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
from palm.runtimes.server.surfaces.rest.validation import PaginationParams, parse_list_flows_query

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


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
    return ok(flow_detail(flow))


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