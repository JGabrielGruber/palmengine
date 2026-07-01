"""Flow execution REST handlers — thin transport over ``ctx.execution.flows``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.handlers import wizard
from palm.runtimes.server.surfaces.rest.responses import accepted

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def create_instance(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body: dict[str, Any] = dict(request.body) if isinstance(request.body, dict) else {}
    if "wizard" in body or "flow" in body:
        submission = body
    else:
        submission = {**body, "flow_name": flow_id}

    try:
        session = ctx.execution.flows.run_wizard(submission)
        view = session.status()
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.submit_failed(str(exc))

    return accepted(_submission_body(view, session.session_id))


def get_instance(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    return wizard.get_wizard(ctx, request, instance_id=instance_id)


def provide_input(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    return wizard.provide_wizard_input(ctx, request, instance_id=instance_id)


def backtrack(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    return wizard.backtrack_wizard(ctx, request, instance_id=instance_id)


def resume_child_wait(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    return wizard.resume_child_wait(ctx, request, instance_id=instance_id)


def _submission_body(view: dict[str, Any], instance_id: str) -> dict[str, Any]:
    return {
        "instance_id": instance_id,
        "job_id": view.get("job_id"),
        "status": view.get("status"),
        "metadata": view.get("metadata") or {},
    }