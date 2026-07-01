"""Flow execution REST handlers — command-path transport over ``dispatch()``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.exceptions import InstanceNotFoundError
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.services.errors import DefinitionNotFoundServiceError, InstanceNotFoundServiceError
from palm.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
)
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.pagination import list_envelope
from palm.runtimes.server.surfaces.rest.responses import accepted, ok, session_context_body
from palm.runtimes.server.surfaces.rest.schema_bridge import body_schema_for_command
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.validation import PaginationParams

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def list_flows(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    rows = ctx.execution.flows.dispatch(["flows"])
    params = PaginationParams(limit=len(rows), offset=0)
    return ok(list_envelope("flows", rows, params))


def describe_flow(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
) -> ServerResponse:
    try:
        row = ctx.execution.flows.dispatch(["flows", flow_id])
    except DefinitionNotFoundServiceError:
        return errors.flow_not_found(flow_id)
    return ok(row if isinstance(row, dict) else {"value": row})


def create_session(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body: dict[str, Any] = dict(request.body) if isinstance(request.body, dict) else {}
    try:
        result = ctx.execution.flows.dispatch(
            ["flows", flow_id, "create"],
            {"body": body},
        )
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.submit_failed(str(exc))

    return accepted(_create_body(result))


def get_session(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
    session_id: str,
) -> ServerResponse:
    try:
        ctx_obj = ctx.execution.flows.dispatch(["flows", flow_id, "session", session_id])
    except (InstanceNotFoundError, InstanceNotFoundServiceError):
        return errors.wizard_not_found(session_id)
    return ok(_session_body(ctx_obj))


def session_input(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
    session_id: str,
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
        ctx_obj = ctx.execution.flows.dispatch(
            ["flows", flow_id, "session", session_id, "input"],
            {"value": body["value"]},
        )
    except InstanceNotFoundError:
        return errors.wizard_not_found(session_id)
    except TypeError as exc:
        return errors.bad_request(str(exc))
    except (ValueError, RuntimeError) as exc:
        return errors.input_rejected(str(exc))

    return ok(_session_body(ctx_obj))


def session_backtrack(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
    session_id: str,
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
        ctx_obj = ctx.execution.flows.dispatch(
            ["flows", flow_id, "session", session_id, "backtrack"],
            {"to_step": body.get("to_step")},
        )
    except InstanceNotFoundError:
        return errors.wizard_not_found(session_id)
    except TypeError as exc:
        return errors.bad_request(str(exc))
    except ValueError as exc:
        return errors.backtrack_rejected(str(exc))

    return ok(_session_body(ctx_obj))


def session_resume(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
    session_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        ctx_obj = ctx.execution.flows.dispatch(
            ["flows", flow_id, "session", session_id, "resume"],
        )
    except InstanceNotFoundError:
        return errors.wizard_not_found(session_id)
    except RuntimeError as exc:
        return errors.input_rejected(str(exc))

    return ok(_session_body(ctx_obj))


def session_resume_child_wait(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
    session_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        ctx_obj = ctx.execution.flows.dispatch(
            ["flows", flow_id, "session", session_id, "resume-child-wait"],
        )
    except InstanceNotFoundError:
        return errors.wizard_not_found(session_id)
    except RuntimeError as exc:
        return errors.input_rejected(str(exc))

    return ok(_session_body(ctx_obj))


def session_cancel(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
    session_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        result = ctx.execution.flows.dispatch(
            ["flows", flow_id, "session", session_id, "cancel"],
        )
    except InstanceNotFoundError:
        return errors.wizard_not_found(session_id)
    except RuntimeError as exc:
        return errors.input_rejected(str(exc))

    return ok(result if isinstance(result, dict) else {"result": result})


def _session_body(ctx_obj: Any) -> dict[str, Any]:
    return session_context_body(ctx_obj)


def _create_body(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        session_id = result.get("session_id")
        return {
            "session_id": session_id,
            "flow_id": result.get("flow_id"),
            "job_id": result.get("job_id"),
            "status": result.get("status"),
        }
    return {"result": result}


__all__ = [
    "create_session",
    "describe_flow",
    "get_session",
    "list_flows",
    "session_backtrack",
    "session_cancel",
    "session_input",
    "session_resume",
    "session_resume_child_wait",
]