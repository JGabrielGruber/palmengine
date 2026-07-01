"""Execution service — coordinates flows, providers, and processes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.services.execution.flows.service import FlowExecutionService
    from palm.services.execution.processes.service import ProcessExecutionService
    from palm.services.execution.providers.service import ProviderExecutionService


class ExecutionService:
    """User execution API — delegates to domain submodules."""

    def __init__(
        self,
        *,
        flows: FlowExecutionService,
        providers: ProviderExecutionService,
        processes: ProcessExecutionService,
    ) -> None:
        self._flows = flows
        self._providers = providers
        self._processes = processes

    @property
    def flows(self) -> FlowExecutionService:
        return self._flows

    @property
    def providers(self) -> ProviderExecutionService:
        return self._providers

    @property
    def processes(self) -> ProcessExecutionService:
        return self._processes


__all__ = ["ExecutionService"]