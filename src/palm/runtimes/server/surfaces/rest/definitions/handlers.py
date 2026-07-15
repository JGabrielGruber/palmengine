"""Definitions service REST handlers — thin transport over ``ctx.definitions``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.services.errors import (
    DefinitionNotFoundServiceError,
    InstanceMigrationServiceError,
    InstanceNotFoundServiceError,
)
from palm.common.surfaces.pagination import list_envelope
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.responses import created, ok
from palm.runtimes.server.surfaces.rest.schema_validation import validate_body
from palm.runtimes.server.surfaces.rest.schemas import VALIDATE_FLOW_BODY
from palm.runtimes.server.surfaces.rest.validation import PaginationParams, parse_list_flows_query

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext


def list_flows(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    query = parse_list_flows_query(request)
    if isinstance(query, ServerResponse):
        return query

    rows = ctx.definitions.list_flows(pattern=query.get("pattern"))
    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("flows", rows, params))


def analyze_flow_impact(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
) -> ServerResponse:
    try:
        payload = ctx.definitions.analyze_impact(
            flow_id,
            target_revision=_revision_query(request),
        )
    except DefinitionNotFoundServiceError:
        return errors.flow_not_found(flow_id)
    return ok(payload)


def migrate_instance(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body

    target_revision = body.get("target_revision")
    if target_revision is None:
        return errors.bad_request("target_revision is required")
    try:
        target = int(target_revision)
    except (TypeError, ValueError):
        return errors.bad_request("target_revision must be an integer")
    if target < 1:
        return errors.bad_request("target_revision must be >= 1")

    dry_run = bool(body.get("dry_run", False))

    try:
        payload = ctx.definitions.migrate_instance(
            instance_id,
            target_revision=target,
            dry_run=dry_run,
        )
    except InstanceNotFoundServiceError:
        return errors.instance_not_found(instance_id)
    except InstanceMigrationServiceError as exc:
        return errors.bad_request(
            exc.reason,
            extra={"blockers": exc.blockers, "result": exc.result},
        )

    return ok(payload)


def get_flow(ctx: ServerContext, request: ServerRequest, *, flow_id: str) -> ServerResponse:
    try:
        payload = ctx.definitions.get_flow(
            flow_id,
            verbose=_verbose_query(request),
            revision=_revision_query(request),
        )
    except DefinitionNotFoundServiceError:
        return errors.flow_not_found(flow_id)
    return ok(payload)


def create_flow(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body

    try:
        payload = ctx.definitions.create_flow(body)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))

    return created({"saved": True, "kind": "flow", "flow": payload})


def update_flow(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body

    try:
        payload = ctx.definitions.update_flow(flow_id, body)
    except DefinitionNotFoundServiceError:
        return errors.flow_not_found(flow_id)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))

    return ok({"saved": True, "kind": "flow", "flow": payload})


def delete_flow(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    flow_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        deleted = ctx.definitions.delete_flow(flow_id)
    except DefinitionNotFoundServiceError:
        return errors.flow_not_found(flow_id)

    return ok({"deleted": deleted, "kind": "flow", "flow_id": flow_id})


def validate_flow(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    from palm.runtimes.server.surfaces.rest.schemas import validate_flow_variant_errors

    body = validate_body(
        request,
        VALIDATE_FLOW_BODY,
        extra_errors=validate_flow_variant_errors(request.body or {}),
    )
    if isinstance(body, ServerResponse):
        return body

    try:
        result = ctx.definitions.validate_flow(body, runtime=ctx.runtime)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    except Exception as exc:
        return errors.validation_failed(
            [{"field": "flow", "message": str(exc), "code": "build_failed"}]
        )

    return ok(result)


def list_processes(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    query = parse_list_flows_query(request)
    if isinstance(query, ServerResponse):
        return query

    rows = ctx.definitions.list_processes()
    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("processes", rows, params))


def get_process(ctx: ServerContext, request: ServerRequest, *, process_id: str) -> ServerResponse:
    try:
        payload = ctx.definitions.get_process(process_id)
    except DefinitionNotFoundServiceError:
        return errors.process_not_found(process_id)
    return ok(payload)


def create_process(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body

    try:
        payload = ctx.definitions.create_process(body)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))

    return created({"saved": True, "kind": "process", "process": payload})


def update_process(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    process_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body

    try:
        payload = ctx.definitions.update_process(process_id, body)
    except DefinitionNotFoundServiceError:
        return errors.process_not_found(process_id)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))

    return ok({"saved": True, "kind": "process", "process": payload})


def delete_process(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    process_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        deleted = ctx.definitions.delete_process(process_id)
    except DefinitionNotFoundServiceError:
        return errors.process_not_found(process_id)

    return ok({"deleted": deleted, "kind": "process", "process_id": process_id})


def list_resources(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    query = parse_list_flows_query(request)
    if isinstance(query, ServerResponse):
        return query

    provider = str(request.query.get("provider") or "").strip() or None
    rows = ctx.definitions.list_resources(provider=provider)
    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("resources", rows, params))


def get_resource(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    resource_ref: str,
) -> ServerResponse:
    try:
        payload = ctx.definitions.get_resource(resource_ref)
    except DefinitionNotFoundServiceError:
        return errors.resource_not_found(resource_ref)
    return ok(payload)


def create_resource(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body

    try:
        payload = ctx.definitions.create_resource(body)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))

    return created({"saved": True, "kind": "resource", "resource": payload})


def update_resource(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    resource_ref: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body

    try:
        payload = ctx.definitions.update_resource(resource_ref, body)
    except DefinitionNotFoundServiceError:
        return errors.resource_not_found(resource_ref)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))

    return ok({"saved": True, "kind": "resource", "resource": payload})


def delete_resource(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    resource_ref: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        deleted = ctx.definitions.delete_resource(resource_ref)
    except DefinitionNotFoundServiceError:
        return errors.resource_not_found(resource_ref)

    return ok({"deleted": deleted, "kind": "resource", "resource_ref": resource_ref})


def _verbose_query(request: ServerRequest) -> bool:
    raw = request.query.get("verbose")
    if raw is None:
        return True
    return str(raw).strip().lower() not in {"0", "false", "no"}


def _revision_query(request: ServerRequest) -> int | None:
    raw = request.query.get("revision")
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    return int(text)


def _json_object(request: ServerRequest) -> dict[str, Any] | ServerResponse:
    body = request.body
    if not isinstance(body, dict):
        return errors.bad_request("JSON object body required")
    return body


__all__ = [
    "create_flow",
    "create_process",
    "create_resource",
    "delete_flow",
    "delete_process",
    "delete_resource",
    "get_flow",
    "get_process",
    "get_resource",
    "list_flows",
    "list_processes",
    "list_resources",
    "migrate_instance",
    "update_flow",
    "update_process",
    "update_resource",
    "validate_flow",
]