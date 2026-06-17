"""Instance endpoints — list, inspect, and resume persisted processes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.cqrs.command import ResumeProcessCommand
from palm.common.cqrs.query import GetInstanceStatusQuery, ListInstancesQuery
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.pagination import list_envelope
from palm.runtimes.server.surfaces.rest.responses import accepted, ok, read_model_body
from palm.runtimes.server.surfaces.rest.validation import PaginationParams, parse_list_instances_query

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def list_instances(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    query = parse_list_instances_query(request)
    if isinstance(query, ServerResponse):
        return query

    rows = ctx.ask(
        ListInstancesQuery(
            status=query.get("status"),
            flow_name=query.get("flow_name"),
            include_terminal=query.get("include_terminal", True),
            limit=None,
        )
    )
    if rows and hasattr(rows[0], "to_dict"):
        rows = [row.to_dict() for row in rows]

    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("instances", rows, params))


def get_instance(ctx: ServerContext, request: ServerRequest, *, instance_id: str) -> ServerResponse:
    row = ctx.ask(GetInstanceStatusQuery(instance_id=instance_id))
    if row is None:
        return errors.instance_not_found(instance_id)
    return ok(read_model_body(row))


def resume_instance(ctx: ServerContext, request: ServerRequest, *, instance_id: str) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        job = ctx.execute(ResumeProcessCommand(instance_id=instance_id))
    except Exception as exc:
        return errors.resume_failed(str(exc))

    ctx.wait_until_idle()
    return accepted(
        {
            "job_id": job.id,
            "status": job.status.value,
            "instance_id": instance_id,
        }
    )