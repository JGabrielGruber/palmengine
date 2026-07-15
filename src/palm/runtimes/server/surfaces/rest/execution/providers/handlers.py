"""Provider execution REST handlers — invoke transport over ``ctx.execution.providers``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.responses import ok

if TYPE_CHECKING:
    from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
    from palm.runtimes.server.context import ServerContext


def invoke_provider(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    provider: str,
    resource_ref: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body: dict[str, Any] = dict(request.body) if isinstance(request.body, dict) else {}
    try:
        payload = ctx.execution.providers.invoke(
            resource_ref,
            provider=provider,
            action=body.get("action"),
            params=body.get("params"),
            state=body.get("state"),
            resource_id=body.get("resource_id"),
        )
    except ValueError as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.submit_failed(str(exc))

    return ok(payload)


def invoke_resource(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    resource_ref: str,
) -> ServerResponse:
    """Shortcut invoke by resource ref only (resolves provider from definition)."""
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body: dict[str, Any] = dict(request.body) if isinstance(request.body, dict) else {}
    try:
        payload = ctx.execution.providers.invoke(
            resource_ref,
            action=body.get("action"),
            params=body.get("params"),
            state=body.get("state"),
            resource_id=body.get("resource_id"),
        )
    except ValueError as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.submit_failed(str(exc))

    return ok(payload)


__all__ = ["invoke_provider", "invoke_resource"]