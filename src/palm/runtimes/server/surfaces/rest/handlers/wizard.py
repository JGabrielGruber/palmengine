"""Wizard endpoints — submit and inspect interactive wizard flows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import SubmitWizardCommand
from palm.common.cqrs.query import GetWizardStatusQuery
from palm.common.job_context import instance_id_for_job
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.responses import accepted, ok, read_model_body
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.schemas import (
    SUBMIT_WIZARD_BODY,
    submit_wizard_variant_errors,
)

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def submit_wizard(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = validate_body(
        request,
        SUBMIT_WIZARD_BODY,
        extra_errors=submit_wizard_variant_errors(request.body or {}),
    )
    if isinstance(body, ServerResponse):
        return body

    try:
        job = ctx.execute(SubmitWizardCommand(body=body))
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.submit_failed(str(exc))

    ctx.wait_until_idle()
    return accepted(_wizard_submission_body(job))


def get_wizard(
    ctx: ServerContext, request: ServerRequest, *, instance_id: str
) -> ServerResponse:
    row = ctx.ask(GetWizardStatusQuery(instance_id=instance_id))
    if row is None:
        return errors.wizard_not_found(instance_id)
    return ok(read_model_body(row))


def _wizard_submission_body(job: Any) -> dict[str, Any]:
    return {
        "instance_id": instance_id_for_job(job),
        "job_id": job.id,
        "status": job.status.value,
        "metadata": job.metadata,
    }