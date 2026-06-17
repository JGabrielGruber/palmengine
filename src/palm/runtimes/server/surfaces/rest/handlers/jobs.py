"""Job endpoints — submit, query, and provide interactive input."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import ProvideInputCommand, SubmitFlowCommand
from palm.common.cqrs.query import GetJobContextQuery, GetJobStatusQuery, ListJobStatusQuery
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.pagination import list_envelope
from palm.runtimes.server.surfaces.rest.responses import job_accepted, ok, read_model_body
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.schemas import (
    PROVIDE_INPUT_BODY,
    SUBMIT_JOB_BODY,
    submit_job_variant_errors,
)
from palm.runtimes.server.surfaces.rest.validation import parse_list_jobs_query

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def get_job(ctx: ServerContext, request: ServerRequest, *, job_id: str) -> ServerResponse:
    result = ctx.ask(GetJobStatusQuery(job_id=job_id))
    if isinstance(result, dict) and not result.get("found", True):
        return errors.job_not_found(job_id)
    return ok(read_model_body(result))


def get_job_context(ctx: ServerContext, request: ServerRequest, *, job_id: str) -> ServerResponse:
    result = ctx.ask(GetJobContextQuery(job_id=job_id))
    if isinstance(result, dict) and not result.get("found", True):
        return errors.job_not_found(job_id)
    return ok(read_model_body(result))


def list_jobs(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    query = parse_list_jobs_query(request)
    if isinstance(query, ServerResponse):
        return query

    rows = ctx.ask(ListJobStatusQuery(status=query.get("status"), limit=None))
    if rows and hasattr(rows[0], "to_dict"):
        rows = [row.to_dict() for row in rows]

    from palm.runtimes.server.surfaces.rest.validation import PaginationParams

    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("jobs", rows, params))


def submit_job(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = validate_body(
        request,
        SUBMIT_JOB_BODY,
        extra_errors=submit_job_variant_errors(request.body or {}),
    )
    if isinstance(body, ServerResponse):
        return body

    try:
        job = ctx.execute(_flow_command_from_body(body))
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.submit_failed(str(exc))

    ctx.wait_until_idle()
    return job_accepted(ctx.runtime.get_job(job.id))


def provide_input(ctx: ServerContext, request: ServerRequest, *, job_id: str) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = validate_body(request, PROVIDE_INPUT_BODY)
    if isinstance(body, ServerResponse):
        return body

    try:
        slug = ctx.execute(ProvideInputCommand(job_id=job_id, value=body["value"]))
    except JobNotFoundError:
        return errors.job_not_found(job_id)
    except (TypeError, RuntimeError) as exc:
        return errors.input_rejected(str(exc))

    ctx.wait_until_idle()
    job_view = ctx.ask(GetJobStatusQuery(job_id=job_id))
    status = job_view.get("status") if isinstance(job_view, dict) else getattr(job_view, "status", "")
    step = job_view.get("step") if isinstance(job_view, dict) else None
    return ok(
        {
            "job_id": job_id,
            "slug": slug,
            "status": status,
            "step": step,
        }
    )


def _flow_command_from_body(body: dict[str, Any]) -> SubmitFlowCommand:
    if "flow" in body and isinstance(body["flow"], dict):
        payload = dict(body["flow"])
        if body.get("job_id") is not None:
            payload["job_id"] = body["job_id"]
        return SubmitFlowCommand(flow=payload)
    if "wizard" in body:
        return SubmitFlowCommand(
            flow={
                "wizard": body["wizard"],
                **({"job_id": body["job_id"]} if body.get("job_id") is not None else {}),
            }
        )
    if "flow_name" in body:
        return SubmitFlowCommand(
            flow=str(body["flow_name"]),
            by_id=bool(body.get("by_id", False)),
            job_id=_optional_str(body.get("job_id")),
        )
    raise ValueError("expected 'flow', 'wizard', or 'flow_name' in request body")


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None