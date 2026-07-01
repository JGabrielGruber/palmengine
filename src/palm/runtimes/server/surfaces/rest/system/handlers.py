"""System service REST handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.services.errors import InstanceNotFoundServiceError
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.handlers import instances, jobs, meta, snapshots
from palm.runtimes.server.surfaces.rest.responses import ok, read_model_body

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse


def doctor(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return meta.doctor(ctx, request)


def list_jobs(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return jobs.list_jobs(ctx, request)


def get_job(ctx: ServerContext, request: ServerRequest, *, job_id: str) -> ServerResponse:
    return jobs.get_job(ctx, request, job_id=job_id)


def inspect_job(ctx: ServerContext, request: ServerRequest, *, job_id: str) -> ServerResponse:
    return jobs.get_job_context(ctx, request, job_id=job_id)


def cancel_job(ctx: ServerContext, request: ServerRequest, *, job_id: str) -> ServerResponse:
    return jobs.cancel_job(ctx, request, job_id=job_id)


def list_instances(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    return instances.list_instances(ctx, request)


def inspect_instance(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    try:
        view = ctx.system.inspect_instance(instance_id)
    except InstanceNotFoundServiceError:
        return errors.instance_not_found(instance_id)
    return ok(read_model_body(view))


def instance_tree(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    return instances.get_instance_tree(ctx, request, instance_id=instance_id)


def list_snapshots(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    return snapshots.list_snapshots(ctx, request, instance_id=instance_id)


def get_snapshot(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
    snapshot_id: str,
) -> ServerResponse:
    return snapshots.get_snapshot(
        ctx,
        request,
        instance_id=instance_id,
        snapshot_id=snapshot_id,
    )


def resume_instance(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    return instances.resume_instance(ctx, request, instance_id=instance_id)