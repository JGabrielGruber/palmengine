"""Plan endpoints — stage and submit deferred execution plans."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.cqrs.command import PreparePlansCommand, SubmitPlansCommand
from palm.common.exceptions import PlanNotFoundError
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.responses import accepted, created
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.schemas import PREPARE_PLANS_BODY, SUBMIT_PLANS_BODY, prepare_plans_variant_errors

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def prepare_plans(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = validate_body(
        request,
        PREPARE_PLANS_BODY,
        extra_errors=prepare_plans_variant_errors(request.body or {}),
    )
    if isinstance(body, ServerResponse):
        return body

    try:
        result = ctx.execute(PreparePlansCommand(body=body))
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))

    return created(result)


def submit_plans(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = validate_body(request, SUBMIT_PLANS_BODY)
    if isinstance(body, ServerResponse):
        return body

    plan_ids = [str(plan_id) for plan_id in body["plan_ids"]]

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
    return accepted(result)