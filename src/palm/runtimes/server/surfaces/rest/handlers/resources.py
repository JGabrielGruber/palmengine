"""Resource invocation endpoint — invoke registered resource definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.core.resource.result import ProviderResult
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.responses import ok
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.schemas import INVOKE_RESOURCE_BODY
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def invoke_resource(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    """Invoke a resource definition on the hosting runtime."""
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = validate_body(request, INVOKE_RESOURCE_BODY)
    if isinstance(body, ServerResponse):
        return body

    resource_ref = str(body.get("resource_ref") or "").strip()
    if not resource_ref:
        return errors.bad_request("resource_ref is required")

    engine = ctx.runtime.resource
    if not engine.is_initialized:
        engine.initialize()

    state = _resolve_state(body.get("state"))
    result = engine.invoke(
        resource_ref,
        action=body.get("action"),
        params=body.get("params"),
        state=state,
        resource_id=body.get("resource_id"),
    )
    return ok(_provider_result_body(result))


def _resolve_state(raw: Any) -> BlackboardState | None:
    if raw is None:
        return None
    if isinstance(raw, BlackboardState):
        return raw
    if isinstance(raw, dict):
        return BlackboardState(raw)
    return None


def _provider_result_body(result: ProviderResult) -> dict[str, Any]:
    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "metadata": dict(result.metadata),
    }