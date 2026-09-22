"""Workload execution REST handlers — product path over ``ctx.execution.workloads``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from plugins.kits.server.responses import error_response
from palm.core.workload.exceptions import (
    WorkloadError,
    WorkloadNotFoundError,
    WorkloadPolicyError,
    WorkloadSpecError,
    WorkloadStateError,
)
from bundles.standard.runtimes.server.surfaces.rest import errors
from bundles.standard.runtimes.server.surfaces.rest.handlers.base import require_auth
from bundles.standard.runtimes.server.surfaces.rest.responses import created, ok

if TYPE_CHECKING:
    from plugins.kits.server.protocol import ServerRequest, ServerResponse
    from bundles.standard.runtimes.server.context import ServerContext


def _workloads(ctx: ServerContext) -> Any:
    try:
        return ctx.execution.workloads
    except Exception as exc:
        raise RuntimeError(f"execution.workloads unavailable: {exc}") from exc


def _map_error(exc: Exception) -> Any:
    if (refused := errors.maybe_admission_refused(exc)) is not None:
        return refused
    if isinstance(exc, WorkloadNotFoundError):
        return error_response(404, "workload_not_found", str(exc))
    if isinstance(
        exc, WorkloadSpecError | WorkloadPolicyError | WorkloadStateError | ValueError
    ):
        return errors.bad_request(str(exc))
    if isinstance(exc, WorkloadError):
        return errors.submit_failed(str(exc))
    return errors.submit_failed(str(exc))


def start_workload(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    body: dict[str, Any] = dict(request.body) if isinstance(request.body, dict) else {}
    spec = body.get("spec")
    if not isinstance(spec, dict):
        return errors.bad_request("body.spec is required (WorkloadSpec mapping)")
    try:
        payload = _workloads(ctx).start(
            spec,
            owner=body.get("owner"),
            workload_id=body.get("workload_id"),
            idempotency_key=body.get("idempotency_key"),
            host_id=body.get("host_id"),
            runtime_name=body.get("runtime_name"),
        )
    except Exception as exc:
        return _map_error(exc)
    return created(payload)


def get_workload(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    workload_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    refresh = str(request.query.get("refresh") or "").lower() in ("1", "true", "yes")
    try:
        payload = _workloads(ctx).get(
            workload_id,
            refresh=refresh,
            runtime_name=request.query.get("runtime_name"),
        )
    except Exception as exc:
        return _map_error(exc)
    return ok(payload)


def list_workloads(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    q = request.query or {}
    try:
        rows = _workloads(ctx).list(
            job_id=q.get("job_id"),
            instance_id=q.get("instance_id"),
            session_id=q.get("session_id"),
            status=q.get("status"),
            runtime=q.get("runtime"),
            runtime_name=q.get("runtime_name"),
        )
    except Exception as exc:
        return _map_error(exc)
    return ok({"workloads": rows})


def stop_workload(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    workload_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    body: dict[str, Any] = dict(request.body) if isinstance(request.body, dict) else {}
    try:
        payload = _workloads(ctx).stop(
            workload_id,
            runtime_name=body.get("runtime_name"),
        )
    except Exception as exc:
        return _map_error(exc)
    return ok(payload)


def exec_workload(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    workload_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    body: dict[str, Any] = dict(request.body) if isinstance(request.body, dict) else {}
    command = body.get("command")
    if not isinstance(command, list | tuple) or not command:
        return errors.bad_request("body.command must be a non-empty argv list")
    try:
        payload = _workloads(ctx).exec(
            workload_id,
            command,
            timeout_s=body.get("timeout_s"),
            env=body.get("env"),
            runtime_name=body.get("runtime_name"),
        )
    except Exception as exc:
        return _map_error(exc)
    return ok(payload)


def list_workload_runtimes(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    try:
        rows = _workloads(ctx).runtimes(runtime_name=(request.query or {}).get("runtime_name"))
    except Exception as exc:
        return _map_error(exc)
    return ok({"runtimes": rows})


def list_workload_hosts(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    try:
        rows = _workloads(ctx).hosts(runtime_name=(request.query or {}).get("runtime_name"))
    except Exception as exc:
        return _map_error(exc)
    return ok({"hosts": rows})


def workload_doctor(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    try:
        payload = _workloads(ctx).doctor(
            runtime_name=(request.query or {}).get("runtime_name")
        )
    except Exception as exc:
        return _map_error(exc)
    return ok(payload)


__all__ = [
    "exec_workload",
    "get_workload",
    "list_workload_hosts",
    "list_workload_runtimes",
    "list_workloads",
    "start_workload",
    "stop_workload",
    "workload_doctor",
]
