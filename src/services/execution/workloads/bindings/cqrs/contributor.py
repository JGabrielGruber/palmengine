"""Register workload execution on the service CQRS contributor registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.common.cqrs.service_contributors import (
    ServiceCqrsContributor,
    register_service_cqrs_contributor,
)
from services.execution.workloads.bindings.cqrs.registry import (
    WORKLOAD_COMMAND_TYPES,
    WORKLOAD_QUERY_TYPES,
)
from services.execution.workloads.bindings.cqrs.schemas import (
    WORKLOAD_COMMAND_SCHEMAS,
    WORKLOAD_QUERY_SCHEMAS,
)
from services.execution.workloads.bindings.cqrs.wiring import wire_workload_service_cqrs

if TYPE_CHECKING:
    from services.execution.workloads.service import WorkloadExecutionService


@dataclass(frozen=True)
class WorkloadsWireContext:
    workloads: WorkloadExecutionService


def register_workloads_cqrs_contributor() -> None:
    register_service_cqrs_contributor(
        ServiceCqrsContributor(
            service_name="workloads",
            command_types=WORKLOAD_COMMAND_TYPES,
            query_types=WORKLOAD_QUERY_TYPES,
            command_schemas=WORKLOAD_COMMAND_SCHEMAS,
            query_schemas=WORKLOAD_QUERY_SCHEMAS,
            wire=lambda bus, qbus, ctx: wire_workload_service_cqrs(
                bus,
                qbus,
                ctx.workloads if isinstance(ctx, WorkloadsWireContext) else ctx,
            ),
        )
    )


register_workloads_cqrs_contributor()

__all__ = ["WorkloadsWireContext", "register_workloads_cqrs_contributor"]
