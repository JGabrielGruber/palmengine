"""
RuntimeHost — minimal contract between runtimes and the executions layer.

Keeps :class:`~palm.common.executions.executor.DefinitionExecutor` decoupled from any
single runtime implementation (embedded, daemon, server, test doubles).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from palm.core.event import EventEngine
    from palm.core.orchestration import OrchestrationEngine
    from palm.core.resource import ResourceEngine


@runtime_checkable
class RuntimeHost(Protocol):
    """
    Services a runtime must expose for definition-driven job submission.

    Concrete runtimes (:class:`~palm.runtimes.embedded.EmbeddedRuntime`, future
    daemon/server hosts) satisfy this protocol structurally — no inheritance required.
    """

    @property
    def orchestration(self) -> OrchestrationEngine:
        """Job lifecycle coordinator."""

    @property
    def event(self) -> EventEngine:
        """Observability bus used when materializing patterns."""

    @property
    def resource(self) -> ResourceEngine | None:
        """Optional external provider coordinator."""

    @property
    def is_started(self) -> bool:
        """Whether the host has completed startup and accepts submissions."""
