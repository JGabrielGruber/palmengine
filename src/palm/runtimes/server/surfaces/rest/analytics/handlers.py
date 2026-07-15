"""Analytics REST handlers — list / describe / query."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.responses import error_response
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers.base import require_auth
from palm.runtimes.server.surfaces.rest.responses import ok
from palm.services.analytics.errors import AnalyticsDisabledError, AnalyticsError

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext


def list_datasets(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    try:
        rows = ctx.analytics.list_datasets()
    except AnalyticsDisabledError as exc:
        return _from_analytics_error(exc)
    return ok({"datasets": rows, "count": len(rows)})


def describe_dataset(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    dataset: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    ref = str(dataset or "").strip()
    if not ref:
        return errors.bad_request("dataset is required")
    try:
        payload = ctx.analytics.describe(ref)
    except AnalyticsError as exc:
        return _from_analytics_error(exc)
    return ok(payload)


def query(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    body = _json_object(request)
    if isinstance(body, ServerResponse):
        return body
    dataset = str(body.get("dataset") or "").strip()
    if not dataset:
        return errors.bad_request("dataset is required")
    profile = str(body.get("profile") or "table")
    params = body.get("params") if isinstance(body.get("params"), dict) else None
    select = body.get("select") if isinstance(body.get("select"), list) else None
    limit = body.get("limit")
    limit_i = int(limit) if isinstance(limit, int) or (isinstance(limit, str) and str(limit).isdigit()) else None
    series = body.get("series") if isinstance(body.get("series"), dict) else None
    kpi = body.get("kpi") if isinstance(body.get("kpi"), dict) else None
    try:
        payload = ctx.analytics.query(
            dataset,
            profile=profile,
            params=params,
            select=[str(s) for s in select] if select else None,
            limit=limit_i,
            series=series,
            kpi=kpi,
        )
    except AnalyticsError as exc:
        return _from_analytics_error(exc)
    if payload.get("status") == "error":
        return _from_query_error(payload)
    return ok(payload)


def list_dashboards(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    try:
        rows = ctx.analytics.list_dashboards()
    except AnalyticsDisabledError as exc:
        return _from_analytics_error(exc)
    return ok({"dashboards": rows, "count": len(rows)})


def get_dashboard(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    dashboard: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    name = str(dashboard or "").strip()
    if not name:
        return errors.bad_request("dashboard is required")
    try:
        payload = ctx.analytics.get_dashboard(name)
    except AnalyticsError as exc:
        return _from_analytics_error(exc)
    if payload.get("status") == "error":
        return _from_query_error(payload)
    return ok(payload)


def render_dashboard(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    dashboard: str,
) -> ServerResponse:
    auth_error = require_auth(ctx, request)
    if auth_error is not None:
        return auth_error
    name = str(dashboard or "").strip()
    if not name:
        return errors.bad_request("dashboard is required")
    params = None
    if request.method.upper() == "POST":
        body = _json_object(request)
        if isinstance(body, ServerResponse):
            return body
        params = body.get("params") if isinstance(body.get("params"), dict) else None
    try:
        payload = ctx.analytics.render_dashboard(name, params=params)
    except AnalyticsError as exc:
        return _from_analytics_error(exc)
    if payload.get("status") == "error":
        return _from_query_error(payload)
    return ok(payload)


def _from_analytics_error(exc: AnalyticsError) -> ServerResponse:
    return error_response(
        exc.http_status,
        exc.code,
        str(exc),
    )


def _from_query_error(payload: dict[str, Any]) -> ServerResponse:
    code = str(payload.get("code") or "invoke_failed")
    message = str(payload.get("error") or "query failed")
    status = {
        "dataset_not_found": 404,
        "dashboard_not_found": 404,
        "analytics_action_not_allowed": 403,
        "invalid_profile": 400,
        "profile_not_implemented": 400,
        "response_too_large": 413,
        "invoke_failed": 502,
        "analytics_disabled": 503,
        "virtual_transform_failed": 400,
    }.get(code, 400)
    return error_response(
        status,
        code,
        message,
        extra={"dataset": payload.get("dataset")},
    )


def _json_object(request: ServerRequest) -> dict[str, Any] | ServerResponse:
    body = request.body
    if body is None:
        return errors.empty_body()
    if not isinstance(body, dict):
        return errors.invalid_json()
    return body
