"""Wire workload CQRS onto host buses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.cqrs.bus import CommandBus, QueryBus
from services.execution.workloads.bindings.cqrs.handlers import (
    WorkloadCommandHandler,
    WorkloadQueryHandler,
)
from services.execution.workloads.bindings.cqrs.registry import (
    WORKLOAD_COMMAND_TYPES,
    WORKLOAD_QUERY_TYPES,
)

if TYPE_CHECKING:
    from services.execution.workloads.service import WorkloadExecutionService


def wire_workload_service_cqrs(
    command_bus: CommandBus,
    query_bus: QueryBus,
    workloads: WorkloadExecutionService,
) -> None:
    command_handler = WorkloadCommandHandler(workloads)
    query_handler = WorkloadQueryHandler(workloads)
    for command_type in WORKLOAD_COMMAND_TYPES:
        command_bus.register(command_type, command_handler)
    for query_type in WORKLOAD_QUERY_TYPES:
        query_bus.register(query_type, query_handler)


__all__ = ["wire_workload_service_cqrs"]
