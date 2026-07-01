"""Wizard endpoints — submit, inspect, and interact with wizard flows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.exceptions import InstanceNotFoundError
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.services.errors import InstanceNotFoundServiceError
from palm.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
)
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.responses import accepted, ok, read_model_body
from palm.runtimes.server.surfaces.rest.schema_bridge import body_schema_for_command
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
        session = ctx.execution.flows.run_wizard(body)
        view = session.status()
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.submit_failed(str(exc))

    return accepted(_wizard_submission_body(view, session.session_id))


def get_wizard(ctx: ServerContext, request: ServerRequest, *, instance_id: str) -> ServerResponse:
    try:
        row = ctx.system.inspect_instance(instance_id)
    except InstanceNotFoundServiceError:
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

    body_schema = body_schema_for_command(
        ctx.schemas,
        ProvideWizardInputCommand,
        properties=("value",),
    )
    body = validate_body(request, body_schema)
    if isinstance(body, ServerResponse):
        return body

    try:
        ctx_view = ctx.execution.flows.session(None, instance_id).input(body["value"])
        view = ctx_view.to_dict()
    except InstanceNotFoundError:
        return errors.wizard_not_found(instance_id)
    except TypeError as exc:
        return errors.bad_request(str(exc))
    except (ValueError, RuntimeError) as exc:
        return errors.input_rejected(str(exc))

    return ok(view)


def backtrack_wizard(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body_schema = body_schema_for_command(
        ctx.schemas,
        RequestWizardBacktrackCommand,
        properties=("to_step",),
    )
    body = validate_body(request, body_schema)
    if isinstance(body, ServerResponse):
        return body

    try:
        ctx_view = ctx.execution.flows.session(None, instance_id).backtrack(body.get("to_step"))
        view = ctx_view.to_dict()
    except InstanceNotFoundError:
        return errors.wizard_not_found(instance_id)
    except TypeError as exc:
        return errors.bad_request(str(exc))
    except ValueError as exc:
        return errors.backtrack_rejected(str(exc))

    return ok(view)


def resume_child_wait(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        ctx_view = ctx.execution.flows.session(None, instance_id).resume_child_wait()
        view = ctx_view.to_dict()
    except InstanceNotFoundError:
        return errors.wizard_not_found(instance_id)
    except RuntimeError as exc:
        return errors.input_rejected(str(exc))

    return ok(view)


def resume_wizard_tick(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        ctx.execution.flows.session(None, instance_id).resume()
        view = _wizard_view_or_not_found(ctx, instance_id)
    except InstanceNotFoundError:
        return errors.wizard_not_found(instance_id)
    except RuntimeError as exc:
        return errors.input_rejected(str(exc))

    if isinstance(view, ServerResponse):
        return view
    return ok(view)


def _wizard_view_or_not_found(
    ctx: ServerContext, instance_id: str
) -> dict[str, Any] | ServerResponse:
    try:
        row = ctx.system.inspect_instance(instance_id)
    except InstanceNotFoundServiceError:
        return errors.wizard_not_found(instance_id)
    return read_model_body(row)


def _wizard_submission_body(view: dict[str, Any], instance_id: str) -> dict[str, Any]:
    return {
        "instance_id": instance_id,
        "job_id": view.get("job_id"),
        "status": view.get("status"),
        "metadata": view.get("metadata") or {},
    }
