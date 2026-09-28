"""Execution service — coordinates flows, providers, processes, and workloads."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.execution.flows.service import FlowExecutionService
    from services.execution.processes.service import ProcessExecutionService
    from services.execution.providers.service import ProviderExecutionService
    from services.execution.workloads.service import WorkloadExecutionService


class ExecutionService:
    """User execution API — delegates to domain submodules."""

    def __init__(
        self,
        *,
        flows: FlowExecutionService,
        providers: ProviderExecutionService,
        processes: ProcessExecutionService,
        workloads: WorkloadExecutionService | None = None,
    ) -> None:
        self._flows = flows
        self._providers = providers
        self._processes = processes
        self._workloads = workloads

    @property
    def flows(self) -> FlowExecutionService:
        return self._flows

    @property
    def providers(self) -> ProviderExecutionService:
        return self._providers

    @property
    def processes(self) -> ProcessExecutionService:
        return self._processes

    @property
    def workloads(self) -> WorkloadExecutionService:
        if self._workloads is None:
            raise RuntimeError("ExecutionService has no WorkloadExecutionService bound")
        return self._workloads


__all__ = ["ExecutionService"]