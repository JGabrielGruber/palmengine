"""System service REST handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.runtimes.server.surfaces.rest.handlers import jobs, meta

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse


def doctor(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return meta.doctor(ctx, request)


def list_jobs(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return jobs.list_jobs(ctx, request)


def get_job(ctx: ServerContext, request: ServerRequest, *, job_id: str) -> ServerResponse:
    return jobs.get_job(ctx, request, job_id=job_id)