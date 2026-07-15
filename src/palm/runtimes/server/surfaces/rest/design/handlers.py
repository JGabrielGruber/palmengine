"""Design service REST handlers — proposal lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.services.errors import (
    DesignCommitRejectedServiceError,
    DesignProposalNotFoundServiceError,
)
from palm.common.surfaces.pagination import list_envelope
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.responses import ok
from palm.runtimes.server.surfaces.rest.validation import PaginationParams

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext


def list_proposals(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    flow_id = str(request.query.get("flow_id") or "").strip() or None
    rows = ctx.design.list_proposals(flow_id=flow_id)
    params = PaginationParams(limit=len(rows) or 1, offset=0)
    return ok(list_envelope("proposals", rows, params))


def propose_flow(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body

    base_raw = body.get("base_flow_id")
    base_flow_id = str(base_raw) if base_raw is not None else None
    proposal_body = {key: value for key, value in body.items() if key != "base_flow_id"}

    try:
        payload = ctx.design.propose_flow(proposal_body, base_flow_id=base_flow_id)
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))

    return ok(payload)


def propose_dashboard(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    """POST /v1/api/design/dashboards — propose dashboard definition (0.41.2)."""
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body
    base = body.get("base_name") or body.get("base_dashboard_name")
    proposal_body = {
        k: v
        for k, v in body.items()
        if k not in {"base_name", "base_dashboard_name"}
    }
    try:
        payload = ctx.design.propose_dashboard(
            proposal_body,
            base_name=str(base) if base is not None else None,
        )
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    return ok(payload)


def publish_dashboard(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    """POST /v1/api/design/dashboards/publish — one-shot dashboard (0.41.2)."""
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body
    base = body.get("base_name") or body.get("base_dashboard_name")
    proposal_body = {
        k: v
        for k, v in body.items()
        if k not in {"base_name", "base_dashboard_name"}
    }
    try:
        payload = ctx.design.publish_dashboard(
            proposal_body,
            base_name=str(base) if base is not None else None,
        )
    except DesignCommitRejectedServiceError as exc:
        return errors.conflict(str(exc))
    except (TypeError, ValueError, KeyError) as exc:
        return errors.bad_request(str(exc))
    return ok(payload)


def get_proposal(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    proposal_id: str,
) -> ServerResponse:
    try:
        payload = ctx.design.get_proposal(proposal_id)
    except DesignProposalNotFoundServiceError:
        return errors.proposal_not_found(proposal_id)
    return ok(payload)


def discard_proposal(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    proposal_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        payload = ctx.design.discard_proposal(proposal_id)
    except DesignProposalNotFoundServiceError:
        return errors.proposal_not_found(proposal_id)
    return ok(payload)


def validate_proposal(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    proposal_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    try:
        payload = ctx.design.validate_proposal(proposal_id, dry_run=True)
    except DesignProposalNotFoundServiceError:
        return errors.proposal_not_found(proposal_id)
    return ok(payload)


def analyze_proposal_impact(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    proposal_id: str,
) -> ServerResponse:
    try:
        payload = ctx.design.analyze_proposal_impact(proposal_id)
    except DesignProposalNotFoundServiceError:
        return errors.proposal_not_found(proposal_id)
    except DesignCommitRejectedServiceError as exc:
        return errors.bad_request(exc.reason, extra={"blockers": exc.blockers})
    return ok(payload)


def commit_proposal(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    proposal_id: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error

    body = request.body if isinstance(request.body, dict) else {}
    try:
        payload = ctx.design.commit_proposal(
            proposal_id,
            commit_token=body.get("commit_token"),
            input_token=body.get("input_token"),
        )
    except DesignProposalNotFoundServiceError:
        return errors.proposal_not_found(proposal_id)
    except DesignCommitRejectedServiceError as exc:
        return errors.bad_request(exc.reason, extra={"blockers": exc.blockers})
    return ok(payload)


def _json_object(request: ServerRequest) -> dict[str, Any] | ServerResponse:
    body = request.body
    if not isinstance(body, dict):
        return errors.bad_request("JSON object body required")
    return body


__all__ = [
    "analyze_proposal_impact",
    "commit_proposal",
    "discard_proposal",
    "get_proposal",
    "list_proposals",
    "propose_flow",
    "validate_proposal",
]