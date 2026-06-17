"""
REST surface — HTTP JSON API for plans, jobs, and instances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.surfaces.base import BaseSurface
from palm.common.runtimes.server.surfaces.rest import handlers

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.common.runtimes.server.registry import RouteRegistry


class RestSurface(BaseSurface):
    """Default REST interaction model mounted at ``/v1`` and ``/health``."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    @property
    def name(self) -> str:
        return "rest"

    def register(self, registry: RouteRegistry) -> None:
        ctx = self._ctx
        registry.register(
            method="GET",
            path="/health",
            handler=lambda req: handlers.health(ctx, req),
            surface=self.name,
        )
        registry.register(
            method="GET",
            path="/v1/jobs",
            handler=lambda req: handlers.list_jobs(ctx, req),
            surface=self.name,
        )
        registry.register(
            method="GET",
            path="/v1/jobs/{job_id}",
            handler=lambda req, job_id: handlers.get_job(ctx, req, job_id=job_id),
            surface=self.name,
        )
        registry.register(
            method="POST",
            path="/v1/jobs",
            handler=lambda req: handlers.submit_job(ctx, req),
            surface=self.name,
            auth_required=True,
        )
        registry.register(
            method="POST",
            path="/v1/jobs/{job_id}/input",
            handler=lambda req, job_id: handlers.provide_input(ctx, req, job_id=job_id),
            surface=self.name,
            auth_required=True,
        )
        registry.register(
            method="POST",
            path="/v1/plans/prepare",
            handler=lambda req: handlers.prepare_plans(ctx, req),
            surface=self.name,
            auth_required=True,
        )
        registry.register(
            method="POST",
            path="/v1/plans/submit",
            handler=lambda req: handlers.submit_plans(ctx, req),
            surface=self.name,
            auth_required=True,
        )
        registry.register(
            method="GET",
            path="/v1/instances",
            handler=lambda req: handlers.list_instances(ctx, req),
            surface=self.name,
        )
        registry.register(
            method="GET",
            path="/v1/instances/{instance_id}",
            handler=lambda req, instance_id: handlers.get_instance(ctx, req, instance_id=instance_id),
            surface=self.name,
        )
        registry.register(
            method="POST",
            path="/v1/instances/{instance_id}/resume",
            handler=lambda req, instance_id: handlers.resume_instance(ctx, req, instance_id=instance_id),
            surface=self.name,
            auth_required=True,
        )