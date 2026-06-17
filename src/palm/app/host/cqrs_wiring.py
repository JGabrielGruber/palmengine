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
    PreparePlansCommand,
    ProvideInputCommand,
    ResumeProcessCommand,
    SubmitFlowCommand,
    SubmitPlansCommand,
    SubmitProcessCommand,
)
from palm.common.exceptions import PlanNotFoundError
from palm.common.runtimes.server.middleware import current_principal_id
from palm.common.runtimes.server.plans import prepare_flow_from_body, prepare_process_from_body
from palm.common.cqrs.projections.instance_index import InstanceIndexProjection
from palm.common.cqrs.projections.job_status_board import JobStatusBoardProjection
from palm.common.cqrs.projections.wizard_progress import WizardProgressProjection
from palm.common.cqrs.query import (
    GetInstanceStatusQuery,
    GetJobStatusQuery,
    GetWizardProgressQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
    ListWizardProgressQuery,
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
            if isinstance(command.flow, dict):
                runtime = self._app.runtime(runtime_name)
                plan = prepare_flow_from_body(runtime, command.flow)
                return runtime.executor.submit_plan(plan)
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
            if isinstance(command.process, dict):
                runtime = self._app.runtime(runtime_name)
                bundle = prepare_process_from_body(runtime, command.process)
                jobs = runtime.executor.submit_plans(bundle.plans)
                return jobs[0] if len(jobs) == 1 else jobs
            return self._app.submit_process(
                command.process,
                runtime_name=runtime_name,
                by_id=command.by_id,
                job_id=command.job_id,
                state=command.state,
                metadata=command.metadata,
            )
        if isinstance(command, PreparePlansCommand):
            return self._prepare_plans(command)
        if isinstance(command, SubmitPlansCommand):
            return self._submit_plans(command)
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

    def _prepare_plans(self, command: PreparePlansCommand) -> dict[str, Any]:
        runtime = self._resolve_plan_runtime(command.runtime_name)
        body = command.body
        if "process" in body or "process_name" in body:
            bundle = prepare_process_from_body(runtime, body)
            stored = [self._store_plan(runtime, plan) for plan in bundle.plans]
        else:
            plan = prepare_flow_from_body(runtime, body)
            stored = [self._store_plan(runtime, plan)]
        registry = runtime.plan_registry
        return {"plans": [registry.summary(item) for item in stored]}

    def _submit_plans(self, command: SubmitPlansCommand) -> dict[str, Any]:
        runtime = self._resolve_plan_runtime(command.runtime_name)
        jobs = []
        for plan_id in command.plan_ids:
            try:
                plan = runtime.plan_registry.consume(plan_id)
            except PlanNotFoundError as exc:
                raise exc
            jobs.append(runtime.executor.submit_plan(plan))
        return {
            "jobs": [
                {
                    "job_id": job.id,
                    "status": job.status.value,
                    "metadata": job.metadata,
                }
                for job in jobs
            ]
        }

    def _resolve_plan_runtime(self, runtime_name: str | None) -> Any:
        name = runtime_name or "server"
        try:
            runtime = self._app.runtime(name)
        except KeyError:
            runtime = self._app.runtime()
        if not hasattr(runtime, "plan_registry"):
            raise RuntimeError(
                f"Runtime {runtime.runtime_name!r} does not expose plan_registry; "
                "enable the server role or pass runtime_name='server'."
            )
        return runtime

    def _store_plan(self, runtime: Any, plan: Any) -> Any:
        return runtime.plan_registry.store(plan, principal_id=current_principal_id(runtime))


class HostQueryHandlers:
    """Serve read models from projections and authoritative stores."""

    def __init__(
        self,
        *,
        app: PalmApp,
        instances: InstanceIndexProjection,
        wizard_progress: WizardProgressProjection,
        job_board: JobStatusBoardProjection,
        instance_manager: InstanceManager,
    ) -> None:
        self._app = app
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
        if isinstance(query, GetJobStatusQuery):
            return self._get_job(query)
        if isinstance(query, ListJobStatusQuery):
            return self._job_board.list_jobs(query)
        if isinstance(query, ListWizardProgressQuery):
            rows = self._wizard_progress.list_progress(query)
            if not query.active_only:
                return rows
            active_ids = {
                row.instance_id
                for row in self._instances.list_instances(
                    ListInstancesQuery(include_terminal=False)
                )
            }
            return [row for row in rows if row.instance_id in active_ids]
        raise TypeError(f"Unsupported query: {type(query).__name__}")

    def _get_job(self, query: GetJobStatusQuery) -> dict[str, Any]:
        row = self._job_board.get_job(query)
        if row is not None:
            payload = row.to_dict()
            payload["found"] = True
            return payload
        try:
            job = self._app.runtime().get_job(query.job_id)
        except Exception:
            return {"found": False, "job_id": query.job_id}
        payload: dict[str, Any] = {
            "found": True,
            "job_id": job.id,
            "status": job.status.value,
            "metadata": job.metadata,
        }
        if job.result is not None:
            payload["result"] = job.result
        if job.error is not None:
            payload["error"] = str(job.error)
        return payload


def wire_command_bus(bus: CommandBus, app: PalmApp, router: RuntimeRouter) -> None:
    handler = PalmCommandHandlers(app, router)
    for command_type in (
        SubmitFlowCommand,
        SubmitProcessCommand,
        ProvideInputCommand,
        ResumeProcessCommand,
        PreparePlansCommand,
        SubmitPlansCommand,
    ):
        bus.register(command_type, handler)


def wire_query_bus(
    bus: QueryBus,
    *,
    app: PalmApp,
    instances: InstanceIndexProjection,
    wizard_progress: WizardProgressProjection,
    job_board: JobStatusBoardProjection,
    instance_manager: InstanceManager,
) -> None:
    handler = HostQueryHandlers(
        app=app,
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
        GetJobStatusQuery,
        ListJobStatusQuery,
        ListWizardProgressQuery,
    ):
        bus.register(query_type, handler)