"""Workload CQRS handlers — thin transport over WorkloadExecutionService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import Command
from palm.common.cqrs.query import Query
from services.execution.workloads.bindings.cqrs.commands import (
    CancelWorkloadCommand,
    ExecWorkloadCommand,
    StartWorkloadCommand,
    StopWorkloadCommand,
)
from services.execution.workloads.bindings.cqrs.queries import (
    GetWorkloadQuery,
    ListWorkloadHostsQuery,
    ListWorkloadRuntimesQuery,
    ListWorkloadsQuery,
)

if TYPE_CHECKING:
    from services.execution.workloads.service import WorkloadExecutionService


class WorkloadCommandHandler:
    def __init__(self, workloads: WorkloadExecutionService) -> None:
        self._workloads = workloads

    def handle(self, command: Command) -> Any:
        if isinstance(command, StartWorkloadCommand):
            return self._workloads.start(
                command.spec,
                owner=command.owner or None,
                workload_id=command.workload_id,
                idempotency_key=command.idempotency_key,
                host_id=command.host_id,
                runtime_name=command.runtime_name,
            )
        if isinstance(command, ExecWorkloadCommand):
            return self._workloads.exec(
                command.workload_id,
                command.command,
                timeout_s=command.timeout_s,
                env=dict(command.env) if command.env else None,
                runtime_name=command.runtime_name,
            )
        if isinstance(command, StopWorkloadCommand):
            return self._workloads.stop(
                command.workload_id,
                runtime_name=command.runtime_name,
            )
        if isinstance(command, CancelWorkloadCommand):
            return self._workloads.cancel(
                command.workload_id,
                runtime_name=command.runtime_name,
            )
        raise TypeError(f"Unsupported workload command: {type(command).__name__}")


class WorkloadQueryHandler:
    def __init__(self, workloads: WorkloadExecutionService) -> None:
        self._workloads = workloads

    def ask(self, query: Query) -> Any:
        if isinstance(query, GetWorkloadQuery):
            return self._workloads.get(
                query.workload_id,
                refresh=query.refresh,
                runtime_name=query.runtime_name,
            )
        if isinstance(query, ListWorkloadsQuery):
            return self._workloads.list(
                job_id=query.job_id,
                instance_id=query.instance_id,
                session_id=query.session_id,
                status=query.status,
                runtime=query.runtime,
                runtime_name=query.runtime_name,
            )
        if isinstance(query, ListWorkloadHostsQuery):
            return self._workloads.hosts(runtime_name=query.runtime_name)
        if isinstance(query, ListWorkloadRuntimesQuery):
            return self._workloads.runtimes(runtime_name=query.runtime_name)
        raise TypeError(f"Unsupported workload query: {type(query).__name__}")


__all__ = ["WorkloadCommandHandler", "WorkloadQueryHandler"]
