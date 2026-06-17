"""
REST handlers — CQRS-backed endpoints for plans, jobs, and instances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import (
    PreparePlansCommand,
    ProvideInputCommand,
    ResumeProcessCommand,
    SubmitFlowCommand,
    SubmitPlansCommand,
)
from palm.common.cqrs.query import (
    GetInstanceStatusQuery,
    GetJobStatusQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
)
from palm.common.exceptions import PlanNotFoundError
from palm.common.runtimes.server.middleware import authenticate_request
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.openapi import build_openapi_spec
from palm.runtimes.server.surfaces.rest.pagination import list_envelope
from palm.runtimes.server.surfaces.rest.validation import (
    parse_pagination,
    require_body,
    require_fields,
    validate_plan_ids,
)

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def health_with_surfaces(ctx: ServerContext, surface_names: list[str]) -> ServerResponse:
    runtime = ctx.runtime
    payload: dict[str, Any] = {
        "status": "ok",
        "runtime": runtime.runtime_name,
        "version": runtime.version,
        "auth_enforce": runtime.auth_enforce,
        "surfaces": surface_names,
    }
    bridge = getattr(ctx, "webhook_bridge", None)
    if bridge is not None:
        payload["webhook_targets"] = len(bridge.targets)
    return ServerResponse(status=200, body=payload)


def openapi(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return ServerResponse(
        status=200,
        body=build_openapi_spec(version=ctx.runtime.version),
    )


def get_job(ctx: ServerContext, request: ServerRequest, *, job_id: str) -> ServerResponse:
    result = ctx.ask(GetJobStatusQuery(job_id=job_id))
    if isinstance(result, dict) and not result.get("found", True):
        return errors.job_not_found(job_id)
    if hasattr(result, "to_dict"):
        return ServerResponse(status=200, body=result.to_dict())
    return ServerResponse(status=200, body=result)


def list_jobs(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    pagination = parse_pagination(request)
    if isinstance(pagination, ServerResponse):
        return pagination

    status = request.query.get("status")
    rows = ctx.ask(ListJobStatusQuery(status=status, limit=None))
    if rows and hasattr(rows[0], "to_dict"):
        rows = [row.to_dict() for row in rows]

    body = list_envelope("jobs", rows, pagination)
    return ServerResponse(status=200, body=body)


def submit_job(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    if not _require_auth(ctx, request):
        return errors.unauthorized()

    body = require_body(request)
    if isinstance(body, ServerResponse):
        return body

    try:
        job = ctx.execute(_flow_command_from_body(body))
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.submit_failed(str(exc))

    ctx.wait_until_idle()
    job = ctx.runtime.get_job(job.id)
    return ServerResponse(
        status=202,
        body={
            "job_id": job.id,
            "status": job.status.value,
            "metadata": job.metadata,
        },
    )


def prepare_plans(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    if not _require_auth(ctx, request):
        return errors.unauthorized()

    body = require_body(request)
    if isinstance(body, ServerResponse):
        return body

    try:
        result = ctx.execute(PreparePlansCommand(body=body))
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))

    return ServerResponse(status=201, body=result)


def submit_plans(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    if not _require_auth(ctx, request):
        return errors.unauthorized()

    body = require_body(request)
    if isinstance(body, ServerResponse):
        return body

    plan_ids = validate_plan_ids(body)
    if isinstance(plan_ids, ServerResponse):
        return plan_ids

    try:
        result = ctx.execute(SubmitPlansCommand(plan_ids=plan_ids))
    except PlanNotFoundError as exc:
        return errors.plan_not_found(exc.plan_id)
    except Exception as exc:
        return errors.submit_failed(str(exc))

    ctx.wait_until_idle()
    for item in result["jobs"]:
        job = ctx.runtime.get_job(str(item["job_id"]))
        item["status"] = job.status.value
    return ServerResponse(status=202, body=result)


def provide_input(ctx: ServerContext, request: ServerRequest, *, job_id: str) -> ServerResponse:
    if not _require_auth(ctx, request):
        return errors.unauthorized()

    body = require_body(request)
    if isinstance(body, ServerResponse):
        return body

    field_errors = require_fields(body, "value")
    if field_errors is not None:
        return errors.bad_request("missing required fields", details=field_errors)

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
    return ServerResponse(
        status=200,
        body={
            "job_id": job_id,
            "slug": slug,
            "status": status,
            "step": step,
        },
    )


def list_instances(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    pagination = parse_pagination(request)
    if isinstance(pagination, ServerResponse):
        return pagination

    status = request.query.get("status")
    flow_name = request.query.get("flow_name")
    include_terminal = request.query.get("include_terminal", "true").lower() != "false"

    rows = ctx.ask(
        ListInstancesQuery(
            status=status,
            flow_name=flow_name,
            include_terminal=include_terminal,
            limit=None,
        )
    )
    if rows and hasattr(rows[0], "to_dict"):
        rows = [row.to_dict() for row in rows]

    body = list_envelope("instances", rows, pagination)
    return ServerResponse(status=200, body=body)


def get_instance(ctx: ServerContext, request: ServerRequest, *, instance_id: str) -> ServerResponse:
    row = ctx.ask(GetInstanceStatusQuery(instance_id=instance_id))
    if row is None:
        return errors.instance_not_found(instance_id)
    if hasattr(row, "to_dict"):
        return ServerResponse(status=200, body=row.to_dict())
    return ServerResponse(status=200, body=row)


def resume_instance(ctx: ServerContext, request: ServerRequest, *, instance_id: str) -> ServerResponse:
    if not _require_auth(ctx, request):
        return errors.unauthorized()

    try:
        job = ctx.execute(ResumeProcessCommand(instance_id=instance_id))
    except Exception as exc:
        return errors.resume_failed(str(exc))

    ctx.wait_until_idle()
    return ServerResponse(
        status=202,
        body={
            "job_id": job.id,
            "status": job.status.value,
            "instance_id": instance_id,
        },
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


def _require_auth(ctx: ServerContext, request: ServerRequest) -> bool:
    return authenticate_request(ctx.runtime, request.headers)


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None