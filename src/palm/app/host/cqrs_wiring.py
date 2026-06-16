"""
CQRS wiring — register ApplicationHost command and query handlers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.app.host.router import RuntimeRouter
from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.command import (
    Command,
    ProvideInputCommand,
    ResumeProcessCommand,
    SubmitFlowCommand,
    SubmitProcessCommand,
)
from palm.common.cqrs.projections.instance_index import InstanceIndexProjection
from palm.common.cqrs.query import GetInstanceStatusQuery, ListInstancesQuery

if TYPE_CHECKING:
    from palm.app.app import PalmApp


class PalmCommandHandlers:
    """Dispatch host commands through PalmApp with runtime routing."""

    def __init__(self, app: PalmApp, router: RuntimeRouter) -> None:
        self._app = app
        self._router = router

    def handle(self, command: Command) -> Any:
        if isinstance(command, SubmitFlowCommand):
            runtime_name = self._router.route_job_runtime(command.runtime_name)
            return self._app.submit_flow(
                command.flow,
                runtime_name=runtime_name,
                by_id=command.by_id,
                job_id=command.job_id,
                state=command.state,
                metadata=command.metadata,
            )
        if isinstance(command, SubmitProcessCommand):
            runtime_name = self._router.route_job_runtime(command.runtime_name)
            return self._app.submit_process(
                command.process,
                runtime_name=runtime_name,
                by_id=command.by_id,
                job_id=command.job_id,
                state=command.state,
                metadata=command.metadata,
            )
        if isinstance(command, ProvideInputCommand):
            runtime_name = self._router.route_job_runtime(command.runtime_name)
            return self._app.provide_input(
                command.job_id,
                command.value,
                runtime_name=runtime_name,
            )
        if isinstance(command, ResumeProcessCommand):
            runtime_name = self._router.route_job_runtime(command.runtime_name)
            return self._app.resume_process(
                command.instance_id,
                runtime_name=runtime_name,
            )
        raise TypeError(f"Unsupported command: {type(command).__name__}")


class InstanceQueryHandlers:
    """Serve instance queries from the projection read model."""

    def __init__(self, projection: InstanceIndexProjection) -> None:
        self._projection = projection

    def ask(self, query: Any) -> Any:
        if isinstance(query, ListInstancesQuery):
            return self._projection.list_instances(query)
        if isinstance(query, GetInstanceStatusQuery):
            return self._projection.get_instance(query)
        raise TypeError(f"Unsupported query: {type(query).__name__}")


def wire_command_bus(bus: CommandBus, app: PalmApp, router: RuntimeRouter) -> None:
    handler = PalmCommandHandlers(app, router)
    for command_type in (
        SubmitFlowCommand,
        SubmitProcessCommand,
        ProvideInputCommand,
        ResumeProcessCommand,
    ):
        bus.register(command_type, handler)


def wire_query_bus(bus: QueryBus, projection: InstanceIndexProjection) -> None:
    handler = InstanceQueryHandlers(projection)
    bus.register(ListInstancesQuery, handler)
    bus.register(GetInstanceStatusQuery, handler)