"""Wire all registered service-domain CQRS contributors onto buses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.service_contributors import wire_service_cqrs_contributors
from services.definitions.bindings.cqrs.wiring import DefinitionsWireContext
from services.design.bindings.cqrs.contributor import DesignWireContext
from services.execution.workloads.bindings.cqrs.contributor import WorkloadsWireContext

if TYPE_CHECKING:
    from palm.common.cqrs.bus import CommandBus, QueryBus
    from palm.common.managers.instance_manager import InstanceManager
    from palm.common.persistence.definition_repository import DefinitionRepository
    from services.design.service import DesignService
    from services.execution.service import ExecutionService


def wire_all_service_cqrs(
    command_bus: CommandBus,
    query_bus: QueryBus,
    *,
    repository: DefinitionRepository,
    instance_manager: InstanceManager,
    design: DesignService | None,
    execution: ExecutionService | None = None,
) -> None:
    """Register service-domain handlers (definitions, design, workloads)."""
    contexts: dict[str, Any] = {
        "definitions": DefinitionsWireContext(
            repository=repository,
            instance_manager=instance_manager,
        ),
    }
    if design is not None:
        contexts["design"] = DesignWireContext(design=design)
    if execution is not None:
        try:
            contexts["workloads"] = WorkloadsWireContext(workloads=execution.workloads)
        except RuntimeError:
            pass
    wire_service_cqrs_contributors(command_bus, query_bus, contexts)


def wire_all_service_cqrs_from_runtime(
    command_bus: Any,
    query_bus: Any,
    runtime: Any,
    *,
    design: DesignService | None,
    execution: ExecutionService | None = None,
) -> None:
    """Convenience wrapper for standalone :class:`ServerContext` bootstrap."""
    wire_all_service_cqrs(
        command_bus,
        query_bus,
        repository=runtime.repository,
        instance_manager=runtime.instance_manager,
        design=design,
        execution=execution,
    )


__all__ = ["wire_all_service_cqrs", "wire_all_service_cqrs_from_runtime"]