"""Meta endpoints — health, OpenAPI, and API docs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest
from palm.runtimes.server.surfaces.rest.docs import build_docs_html
from palm.runtimes.server.surfaces.rest.openapi import build_openapi_spec
from palm.runtimes.server.surfaces.rest.responses import ok

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def health(ctx: ServerContext, surface_names: list[str]) -> Any:
    runtime = ctx.runtime
    payload: dict[str, Any] = {
        "status": "ok",
        "runtime": runtime.runtime_name,
        "version": runtime.version,
        "auth_enforce": runtime.auth_enforce,
        "surfaces": surface_names,
        "docs": "/v1/docs",
        "explorer": "/explorer",
        "wiki": "/explorer",
        "openapi": "/v1/openapi.json",
    }
    bridge = getattr(ctx, "webhook_bridge", None)
    if bridge is not None:
        payload["webhook_targets"] = len(bridge.targets)
    return ok(payload)


def openapi(ctx: ServerContext, request: ServerRequest) -> Any:
    return ok(build_openapi_spec(version=ctx.runtime.version))


def docs(ctx: ServerContext, request: ServerRequest) -> Any:
    from palm.runtimes.server.surfaces.rest.responses import html as html_response

    return html_response(build_docs_html(version=ctx.runtime.version))