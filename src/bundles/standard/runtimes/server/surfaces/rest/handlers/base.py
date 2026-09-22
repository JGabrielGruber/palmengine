"""Shared REST handler utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from plugins.kits.server.middleware import authenticate_request
from plugins.kits.server.protocol import ServerRequest, ServerResponse
from bundles.standard.runtimes.server.surfaces.rest import errors

if TYPE_CHECKING:
    from bundles.standard.runtimes.server.context import ServerContext


def require_auth(ctx: ServerContext, request: ServerRequest) -> ServerResponse | None:
    """Return an error response when auth is required but missing."""
    if authenticate_request(ctx.runtime, request.headers):
        return None
    return errors.unauthorized()
