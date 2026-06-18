"""Wizard endpoints — submit, inspect, and interact with wizard flows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
    SubmitWizardCommand,
)
from palm.common.cqrs.query import GetWizardStatusQuery
from palm.common.exceptions import InstanceNotFoundError
from palm.common.job_context import instance_id_for_job
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.responses import accepted, ok, read_model_body
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.schemas import (
    SUBMIT_WIZARD_BODY,
    WIZARD_BACKTRACK_BODY,
    WIZARD_INPUT_BODY,
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


def provide_wizard_input(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = validate_body(request, WIZARD_INPUT_BODY)
    if isinstance(body, ServerResponse):
        return body

    try:
        result = ctx.execute(
            ProvideWizardInputCommand(instance_id=instance_id, value=body["value"])
        )
    except InstanceNotFoundError:
        return errors.wizard_not_found(instance_id)
    except TypeError as exc:
        return errors.bad_request(str(exc))
    except (ValueError, RuntimeError) as exc:
        return errors.input_rejected(str(exc))

    ctx.wait_until_idle()
    view = _wizard_view_or_not_found(ctx, instance_id)
    if isinstance(view, ServerResponse):
        return view
    return ok(_merge_interaction(view, slug=result.get("slug")))


def backtrack_wizard(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = validate_body(request, WIZARD_BACKTRACK_BODY)
    if isinstance(body, ServerResponse):
        return body

    try:
        result = ctx.execute(
            RequestWizardBacktrackCommand(
                instance_id=instance_id,
                to_step=body.get("to_step"),
            )
        )
    except InstanceNotFoundError:
        return errors.wizard_not_found(instance_id)
    except TypeError as exc:
        return errors.bad_request(str(exc))
    except ValueError as exc:
        return errors.backtrack_rejected(str(exc))

    ctx.wait_until_idle()
    view = _wizard_view_or_not_found(ctx, instance_id)
    if isinstance(view, ServerResponse):
        return view
    return ok(_merge_interaction(view, to_step=result.get("to_step")))


def _wizard_view_or_not_found(
    ctx: ServerContext, instance_id: str
) -> dict[str, Any] | ServerResponse:
    row = ctx.ask(GetWizardStatusQuery(instance_id=instance_id))
    if row is None:
        return errors.wizard_not_found(instance_id)
    return read_model_body(row)


def _merge_interaction(
    view: dict[str, Any],
    *,
    slug: str | None = None,
    to_step: str | None = None,
) -> dict[str, Any]:
    payload = dict(view)
    if slug is not None:
        payload["slug"] = slug
    if to_step is not None:
        payload["to_step"] = to_step
    return payload


def _wizard_submission_body(job: Any) -> dict[str, Any]:
    return {
        "instance_id": instance_id_for_job(job),
        "job_id": job.id,
        "status": job.status.value,
        "metadata": job.metadata,
    }