"""
CQRS wiring — register ApplicationHost command and query handlers.

**Adding a command:** define a dataclass in :mod:`palm.common.cqrs.command`,
handle it in :class:`PalmCommandHandlers`, and call
:func:`wire_command_bus` (or ``bus.register``) at host startup.

**Adding a query:** define a dataclass in :mod:`palm.common.cqrs.query`, read
from a projection (or authoritative store) in :class:`HostQueryHandlers`, and
register the handler in :func:`wire_query_bus`.
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
from palm.common.cqrs.projections.job_status_board import JobStatusBoardProjection
from palm.common.cqrs.projections.wizard_progress import WizardProgressProjection
from palm.common.cqrs.query import (
    GetInstanceStatusQuery,
    GetWizardProgressQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
)

if TYPE_CHECKING:
    from palm.app.app import PalmApp
    from palm.common.managers.instance_manager import InstanceManager


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


class HostQueryHandlers:
    """Serve read models from projections and authoritative stores."""

    def __init__(
        self,
        *,
        instances: InstanceIndexProjection,
        wizard_progress: WizardProgressProjection,
        job_board: JobStatusBoardProjection,
        instance_manager: InstanceManager,
    ) -> None:
        self._instances = instances
        self._wizard_progress = wizard_progress
        self._job_board = job_board
        self._instance_manager = instance_manager

    def ask(self, query: Any) -> Any:
        if isinstance(query, ListInstancesQuery):
            return self._instances.list_instances(query)
        if isinstance(query, GetInstanceStatusQuery):
            return self._instances.get_instance(query)
        if isinstance(query, ListInstanceSnapshotsQuery):
            return self._instance_manager.list_state_snapshots(query.instance_id)
        if isinstance(query, GetWizardProgressQuery):
            return self._wizard_progress.get_progress(query)
        if isinstance(query, ListJobStatusQuery):
            return self._job_board.list_jobs(query)
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


def wire_query_bus(
    bus: QueryBus,
    *,
    instances: InstanceIndexProjection,
    wizard_progress: WizardProgressProjection,
    job_board: JobStatusBoardProjection,
    instance_manager: InstanceManager,
) -> None:
    handler = HostQueryHandlers(
        instances=instances,
        wizard_progress=wizard_progress,
        job_board=job_board,
        instance_manager=instance_manager,
    )
    for query_type in (
        ListInstancesQuery,
        GetInstanceStatusQuery,
        ListInstanceSnapshotsQuery,
        GetWizardProgressQuery,
        ListJobStatusQuery,
    ):
        bus.register(query_type, handler)