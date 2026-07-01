"""Definitions service REST handlers — thin transport over ``ctx.definitions``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.handlers import catalog, resources

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse


def list_flows(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return catalog.list_flows(ctx, request)


def get_flow(ctx: ServerContext, request: ServerRequest, *, flow_id: str) -> ServerResponse:
    return catalog.get_flow(ctx, request, flow_id=flow_id)


def validate_flow(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return catalog.validate_flow(ctx, request)


def list_processes(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return catalog.list_processes(ctx, request)


def get_process(ctx: ServerContext, request: ServerRequest, *, process_id: str) -> ServerResponse:
    return catalog.get_process(ctx, request, process_id=process_id)


def list_resources(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return resources.list_resources(ctx, request)


def get_resource(ctx: ServerContext, request: ServerRequest, *, resource_ref: str) -> ServerResponse:
    return resources.get_resource(ctx, request, resource_ref=resource_ref)