"""Resource catalog and invocation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.core.resource.result import ProviderResult
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.pagination import list_envelope
from palm.runtimes.server.surfaces.rest.responses import ok
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.schemas import INVOKE_RESOURCE_BODY
from palm.runtimes.server.surfaces.rest.validation import PaginationParams, parse_list_flows_query
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def list_resources(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    query = parse_list_flows_query(request)
    if isinstance(query, ServerResponse):
        return query

    provider = str(request.query.get("provider") or "").strip() or None
    rows = ctx.definition.list_resources(provider=provider)
    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("resources", rows, params))


def get_resource(ctx: ServerContext, request: ServerRequest, *, resource_ref: str) -> ServerResponse:
    try:
        payload = ctx.definition.get_resource(resource_ref)
    except DefinitionNotFoundServiceError:
        return errors.resource_not_found(resource_ref)
    return ok(payload)


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


