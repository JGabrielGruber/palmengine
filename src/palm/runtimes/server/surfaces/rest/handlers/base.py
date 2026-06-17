"""Shared REST handler utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.middleware import authenticate_request
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.runtimes.server.surfaces.rest import errors

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def require_auth(ctx: ServerContext, request: ServerRequest) -> ServerResponse | None:
    """Return an error response when auth is required but missing."""
    if authenticate_request(ctx.runtime, request.headers):
        return None
    return errors.unauthorized()
