"""Flow execution REST handlers — command-path transport over ``dispatch()``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.exceptions import InstanceNotFoundError, MutationRejectedError
from palm.common.operator.flow_session_view import shape_flow_session_view
from palm.common.operator.invoke_tree import build_invoke_tree
from plugins.kits.server.protocol import ServerRequest, ServerResponse
from palm.common.services.errors import DefinitionNotFoundServiceError, InstanceNotFoundServiceError
from palm.common.surfaces.pagination import list_envelope
from plugins.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
)
from bundles.standard.runtimes.server.surfaces.rest import errors
from bundles.standard.runtimes.server.surfaces.rest.handlers.base import require_auth
from bundles.standard.runtimes.server.surfaces.rest.responses import accepted, flatten_session_context, ok
from bundles.standard.runtimes.server.surfaces.rest.schema_bridge import body_schema_for_command
from bundles.standard.runtimes.server.surfaces.rest.schema_validation import validate_body
from bundles.standard.runtimes.server.surfaces.rest.validation import PaginationParams
from palm.services.assist.views import resolve_view_format

if TYPE_CHECKING:
    from bundles.standard.runtimes.server.context import ServerContext


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
    # Cookie-like system session transport (0.58.7) — same contract as WS bind
    from plugins.kits.server.middleware import (
        extract_system_session_hint,
        set_cookie_header_value,
    )

    # Cookie/header → edge session_id (system subject only, 0.58.9).
    if not body.get("session_id") or not str(body.get("session_id", "")).startswith(
        "sess-"
    ):
        hint = extract_system_session_hint(request.headers)
        if hint:
            body["session_id"] = hint
    try:
        result = ctx.execution.flows.dispatch(
            ["flows", flow_id, "create"],
            {"body": body},
        )
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        if (refused := errors.maybe_admission_refused(exc)) is not None:
            return refused
        return errors.submit_failed(str(exc))

    payload = _create_body(result)
    headers: dict[str, str] = {}
    system_sid = payload.get("session_id")
    if system_sid and str(system_sid).startswith("sess-"):
        headers["Set-Cookie"] = set_cookie_header_value(str(system_sid))
        headers["X-Palm-Session"] = str(system_sid)
    return accepted(payload, headers=headers if headers else None)


def get_instance(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
    instance_id: str,
) -> ServerResponse:
    try:
        ctx_obj = ctx.execution.flows.dispatch(["flows", flow_id, "instance", instance_id])
    except (InstanceNotFoundError, InstanceNotFoundServiceError):
        return errors.wizard_not_found(instance_id)
    return ok(_session_body(ctx, request, ctx_obj, flow_id=flow_id, instance_id=instance_id))


def instance_input(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
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

    input_params: dict[str, Any] = {"value": body["value"]}
    raw_body = request.body if isinstance(request.body, dict) else {}
    if raw_body.get("input_token") is not None:
        input_params["input_token"] = raw_body["input_token"]
    try:
        ctx_obj = ctx.execution.flows.dispatch(
            ["flows", flow_id, "instance", instance_id, "input"],
            input_params,
        )
    except (InstanceNotFoundError, InstanceNotFoundServiceError):
        return errors.wizard_not_found(instance_id)
    except MutationRejectedError as exc:
        return errors.input_rejected(str(exc))
    except TypeError as exc:
        return errors.bad_request(str(exc))
    except (ValueError, RuntimeError) as exc:
        if (refused := errors.maybe_admission_refused(exc)) is not None:
            return refused
        return errors.input_rejected(str(exc))

    return ok(_session_body(ctx, request, ctx_obj, flow_id=flow_id, instance_id=instance_id))


def instance_backtrack(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
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
        ctx_obj = ctx.execution.flows.dispatch(
            ["flows", flow_id, "instance", instance_id, "backtrack"],
            {"to_step": body.get("to_step")},
        )
    except (InstanceNotFoundError, InstanceNotFoundServiceError):
        return errors.wizard_not_found(instance_id)
    except TypeError as exc:
        return errors.bad_request(str(exc))
    except ValueError as exc:
        return errors.backtrack_rejected(str(exc))
    except RuntimeError as exc:
        if (refused := errors.maybe_admission_refused(exc)) is not None:
            return refused
        return errors.backtrack_rejected(str(exc))

    return ok(_session_body(ctx, request, ctx_obj, flow_id=flow_id, instance_id=instance_id))


def instance_resume(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
    instance_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        ctx_obj = ctx.execution.flows.dispatch(
            ["flows", flow_id, "instance", instance_id, "resume"],
        )
    except (InstanceNotFoundError, InstanceNotFoundServiceError):
        return errors.wizard_not_found(instance_id)
    except RuntimeError as exc:
        if (refused := errors.maybe_admission_refused(exc)) is not None:
            return refused
        return errors.input_rejected(str(exc))

    return ok(_session_body(ctx, request, ctx_obj, flow_id=flow_id, instance_id=instance_id))


def instance_cancel(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
    instance_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        result = ctx.execution.flows.dispatch(
            ["flows", flow_id, "instance", instance_id, "cancel"],
        )
    except (InstanceNotFoundError, InstanceNotFoundServiceError):
        return errors.wizard_not_found(instance_id)
    except RuntimeError as exc:
        return errors.input_rejected(str(exc))

    return ok(result if isinstance(result, dict) else {"result": result})


def _view_format(request: ServerRequest) -> str:
    query = dict(request.query) if request.query else {}
    return resolve_view_format(query, default="powertool")


def _session_body(
    ctx: ServerContext,
    request: ServerRequest,
    ctx_obj: Any,
    *,
    flow_id: str | None = None,
    instance_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    flat = flatten_session_context(ctx_obj)
    view_format = _view_format(request)
    # Product continue key is instance_id (0.58.19); session_id kw is legacy alias.
    continue_hint = instance_id if instance_id is not None else session_id
    instance_key = (
        flat.get("instance_id")
        or (
            continue_hint
            if continue_hint and not str(continue_hint).startswith("sess-")
            else None
        )
    )
    if instance_key is None and continue_hint and str(continue_hint).startswith("sess-"):
        try:
            instance_key = ctx.execution.flows._resolve_instance_id(str(continue_hint))
        except Exception:
            instance_key = None
    if instance_key is None:
        raw = continue_hint or flat.get("session_id")
        if raw is not None and not str(raw).startswith("sess-"):
            instance_key = raw
    invoke_tree = None
    if view_format == "assistant" and instance_key is not None:
        invoke_tree = build_invoke_tree(ctx.runtime, str(instance_key), base_url=None)
    stored_gate = None
    if instance_key is not None:
        meta = ctx.execution.flows.get_instance_metadata(str(instance_key))
        gate = meta.get("mutation_gate")
        stored_gate = gate if isinstance(gate, dict) else None
    return shape_flow_session_view(
        flat,
        format=view_format,
        session_id=str(instance_key) if instance_key is not None else session_id,
        flow_id=flow_id or flat.get("flow_name"),
        invoke_tree=invoke_tree,
        stored_mutation_gate=stored_gate,
    )


def _create_body(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        # 0.58.9: session_id = system; instance_id = continue handle.
        body: dict[str, Any] = {
            "flow_id": result.get("flow_id"),
            "job_id": result.get("job_id"),
            "status": result.get("status"),
        }
        if result.get("instance_id") is not None:
            body["instance_id"] = result["instance_id"]
        sid = result.get("session_id")
        if sid is not None and str(sid).startswith("sess-"):
            body["session_id"] = sid
        return body
    return {"result": result}


__all__ = [
    "create_session",
    "describe_flow",
    "get_instance",
    "list_flows",
    "instance_backtrack",
    "instance_cancel",
    "instance_input",
    "instance_resume",
]