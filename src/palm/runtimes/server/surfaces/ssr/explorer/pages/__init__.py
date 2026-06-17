"""Focused Explorer page modules and route dispatcher."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse

from .base import PageContext
from .flows import FlowPages
from .instances import InstancePages
from .jobs import JobPages
from .overview import OverviewPages
from .patterns import PatternPages
from .processes import ProcessPages
from .resources import ResourcePages
from .schemas import SchemaPages

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext

__all__ = [
    "ExplorerPages",
    "FlowPages",
    "InstancePages",
    "JobPages",
    "OverviewPages",
    "PageContext",
    "PatternPages",
    "ProcessPages",
    "ResourcePages",
    "SchemaPages",
]


class ExplorerPages:
    """Server-rendered Explorer routes backed by CQRS read models."""

    def __init__(self, ctx: ServerContext) -> None:
        page_ctx = PageContext.from_server(ctx)
        self._overview = OverviewPages(page_ctx)
        self._flows = FlowPages(page_ctx)
        self._processes = ProcessPages(page_ctx)
        self._resources = ResourcePages(page_ctx)
        self._patterns = PatternPages(page_ctx)
        self._schemas = SchemaPages(page_ctx)
        self._jobs = JobPages(page_ctx)
        self._instances = InstancePages(page_ctx)

    def overview(self, request: ServerRequest) -> ServerResponse:
        return self._overview.overview(request)

    def flows(self, request: ServerRequest) -> ServerResponse:
        return self._flows.catalog(request)

    def flow_submit(self, request: ServerRequest) -> ServerResponse:
        return self._flows.submit(request)

    def flow_detail(self, request: ServerRequest, *, flow_id: str) -> ServerResponse:
        return self._flows.detail(request, flow_id=flow_id)

    def processes(self, request: ServerRequest) -> ServerResponse:
        return self._processes.catalog(request)

    def process_detail(self, request: ServerRequest, *, process_id: str) -> ServerResponse:
        return self._processes.detail(request, process_id=process_id)

    def resources(self, request: ServerRequest) -> ServerResponse:
        return self._resources.catalog(request)

    def resource_detail(self, request: ServerRequest, *, resource_id: str) -> ServerResponse:
        return self._resources.detail(request, resource_id=resource_id)

    def patterns(self, request: ServerRequest) -> ServerResponse:
        return self._patterns.catalog(request)

    def schemas(self, request: ServerRequest) -> ServerResponse:
        return self._schemas.catalog(request)

    def jobs(self, request: ServerRequest) -> ServerResponse:
        return self._jobs.catalog(request)

    def job_detail(self, request: ServerRequest, *, job_id: str) -> ServerResponse:
        return self._jobs.detail(request, job_id=job_id)

    def instances(self, request: ServerRequest) -> ServerResponse:
        return self._instances.catalog(request)

    def instance_detail(self, request: ServerRequest, *, instance_id: str) -> ServerResponse:
        return self._instances.detail(request, instance_id=instance_id)

    def snapshots(self, request: ServerRequest, *, instance_id: str) -> ServerResponse:
        return self._instances.snapshots(request, instance_id=instance_id)

    def snapshot_detail(
        self,
        request: ServerRequest,
        *,
        instance_id: str,
        snapshot_id: str,
    ) -> ServerResponse:
        return self._instances.snapshot_detail(
            request,
            instance_id=instance_id,
            snapshot_id=snapshot_id,
        )