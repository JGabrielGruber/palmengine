"""Assist REST handlers — command-path transport over ``dispatch()``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.exceptions import InstanceNotFoundError, MutationRejectedError
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.services.errors import DefinitionNotFoundServiceError, InstanceNotFoundServiceError
from palm.common.surfaces.pagination import list_envelope
from palm.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
)
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.responses import accepted, ok
from palm.runtimes.server.surfaces.rest.schema_bridge import body_schema_for_command
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.validation import PaginationParams
from palm.services.assist.views import resolve_view_format

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext


def list_scenarios(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    rows = ctx.assist.dispatch(["assist", "scenarios"])
    params = PaginationParams(limit=len(rows), offset=0)
    return ok(list_envelope("scenarios", rows, params))


def describe_scenario(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    scenario_id: str,
) -> ServerResponse:
    try:
        row = ctx.assist.dispatch(["assist", "scenarios", scenario_id])
    except DefinitionNotFoundServiceError:
        return errors.scenario_not_found(scenario_id)
    return ok(row if isinstance(row, dict) else {"value": row})


def start_scenario(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    scenario_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body: dict[str, Any] = dict(request.body) if isinstance(request.body, dict) else {}
    try:
        result = ctx.assist.dispatch(
            ["assist", "scenarios", scenario_id, "start"],
            {"body": body, "format": _view_format(request)},
        )
    except DefinitionNotFoundServiceError:
        return errors.scenario_not_found(scenario_id)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.submit_failed(str(exc))

    return accepted(_start_body(result))


def get_session(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    session_id: str,
) -> ServerResponse:
    try:
        body = ctx.assist.dispatch(
            ["assist", "session", session_id],
            {"format": _view_format(request)},
        )
    except (InstanceNotFoundError, InstanceNotFoundServiceError):
        return errors.wizard_not_found(session_id)
    return ok(body if isinstance(body, dict) else {"value": body})


def session_input(
    ctx: ServerContext,
    request: ServerRequest,
    *,
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

    input_params: dict[str, Any] = {
        "value": body["value"],
        "format": _view_format(request),
    }
    raw_body = request.body if isinstance(request.body, dict) else {}
    if raw_body.get("input_token") is not None:
        input_params["input_token"] = raw_body["input_token"]
    try:
        result = ctx.assist.dispatch(
            ["assist", "session", session_id, "input"],
            input_params,
        )
    except InstanceNotFoundError:
        return errors.wizard_not_found(session_id)
    except MutationRejectedError as exc:
        return errors.input_rejected(str(exc))
    except TypeError as exc:
        return errors.bad_request(str(exc))
    except (ValueError, RuntimeError) as exc:
        return errors.input_rejected(str(exc))

    return ok(result if isinstance(result, dict) else {"value": result})


def session_backtrack(
    ctx: ServerContext,
    request: ServerRequest,
    *,
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
        result = ctx.assist.dispatch(
            ["assist", "session", session_id, "backtrack"],
            {"to_step": body.get("to_step"), "format": _view_format(request)},
        )
    except InstanceNotFoundError:
        return errors.wizard_not_found(session_id)
    except TypeError as exc:
        return errors.bad_request(str(exc))
    except ValueError as exc:
        return errors.backtrack_rejected(str(exc))

    return ok(result if isinstance(result, dict) else {"value": result})


def session_resume(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    session_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        result = ctx.assist.dispatch(
            ["assist", "session", session_id, "resume"],
            {"format": _view_format(request)},
        )
    except InstanceNotFoundError:
        return errors.wizard_not_found(session_id)
    except RuntimeError as exc:
        return errors.input_rejected(str(exc))

    return ok(result if isinstance(result, dict) else {"value": result})


def session_cancel(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    session_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        result = ctx.assist.dispatch(["assist", "session", session_id, "cancel"])
    except InstanceNotFoundError:
        return errors.wizard_not_found(session_id)
    except RuntimeError as exc:
        return errors.input_rejected(str(exc))

    return ok(result if isinstance(result, dict) else {"result": result})


def session_handoff(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    session_id: str,
) -> ServerResponse:
    try:
        result = ctx.assist.dispatch(["assist", "session", session_id, "handoff"])
    except (InstanceNotFoundError, InstanceNotFoundServiceError):
        return errors.wizard_not_found(session_id)
    return ok(result if isinstance(result, dict) else {"value": result})


def doctor(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return ok(ctx.assist.dispatch(["assist", "doctor"]))


def catalog_flows(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    rows = ctx.assist.dispatch(["assist", "catalog", "flows"])
    if not isinstance(rows, list):
        rows = list(rows) if rows else []
    params = PaginationParams(limit=len(rows), offset=0)
    return ok(list_envelope("flows", rows, params))


def _view_format(request: ServerRequest) -> str:
    query = dict(request.query) if request.query else {}
    return resolve_view_format(query)


def _start_body(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return dict(result)
    return {"result": result}


__all__ = [
    "catalog_flows",
    "describe_scenario",
    "doctor",
    "get_session",
    "list_scenarios",
    "session_backtrack",
    "session_cancel",
    "session_handoff",
    "session_input",
    "session_resume",
    "start_scenario",
]