"""
CQRS wiring — register ApplicationHost command and query handlers.

**Adding a command:** define a dataclass in the pattern app (or
:mod:`palm.common.cqrs.command` for generic commands), register a
:class:`~palm.patterns._registry.CqrsContributor`, and ensure the pattern
app is loaded via :func:`palm.patterns._apps.autoload`.

**Adding a query:** same pattern — contributor ``query_types`` and
``handle_query`` dispatch through :class:`HostQueryHandlers`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import palm.patterns  # noqa: F401 — ensure pattern CQRS contributors are registered
from palm.app.host.router import RuntimeRouter
from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.command import (
    CancelJobCommand,
    Command,
    MigrateInstanceCommand,
    PreparePlansCommand,
    ProvideInputCommand,
    ResumeProcessCommand,
    SubmitFlowCommand,
    SubmitPlansCommand,
    SubmitProcessCommand,
)
from palm.common.cqrs.instance_inspect import handle_inspect_instance
from palm.common.cqrs.projections.instance_index import InstanceIndexProjection
from palm.common.cqrs.projections.job_status_board import JobStatusBoardProjection
from palm.common.cqrs.projections.resource_invocation import ResourceInvocationProjection
from palm.common.cqrs.query import (
    AnalyzeDefinitionImpactQuery,
    GetFlowQuery,
    GetInstanceSnapshotQuery,
    GetInstanceStatusQuery,
    GetJobContextQuery,
    GetJobStatusQuery,
    GetProcessQuery,
    GetResourceInvocationsQuery,
    InspectInstanceQuery,
    ListFlowsQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
    ListProcessesQuery,
    ListResourceInvocationsQuery,
)
from palm.common.cqrs.resolvers import resolve_flow, resolve_process, resolve_snapshot
from palm.common.exceptions import DefinitionNotFoundError, InstanceNotFoundError, PlanNotFoundError
from palm.common.job_context import build_job_context, instance_id_for_job
from palm.common.runtimes.server.middleware import current_principal_id
from palm.common.runtimes.server.plans import prepare_flow_from_body, prepare_process_from_body
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.patterns._registry import iter_cqrs_contributors
from palm.patterns.wizard.bindings.cqrs.queries import GetWizardProgressQuery

if TYPE_CHECKING:
    from palm.app.app import PalmApp
    from palm.common.cqrs.projection import Projection
    from palm.common.managers.instance_manager import InstanceManager
    from palm.definitions.flow import FlowDefinition
    from palm.definitions.process import ProcessDefinition
    from palm.instances import StateSnapshot


class PalmCommandHandlers:
    """Dispatch host commands through PalmApp with runtime routing."""

    def __init__(self, app: PalmApp, router: RuntimeRouter) -> None:
        self._app = app
        self._router = router

    def handle(self, command: Command) -> Any:
        for contributor in iter_cqrs_contributors():
            if contributor.handle_command is None:
                continue
            if isinstance(command, contributor.command_types):
                return contributor.handle_command(command, self)

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
        if isinstance(command, CancelJobCommand):
            runtime_name = self._router.route_job_runtime(command.runtime_name)
            runtime = self._app.runtime(runtime_name)
            try:
                cancelled = runtime.cancel_job(command.job_id)
            except JobNotFoundError:
                return {"found": False, "job_id": command.job_id}
            job = runtime.get_job(command.job_id)
            return {
                "found": True,
                "job_id": command.job_id,
                "cancelled": cancelled,
                "status": job.status.value,
            }
        if isinstance(command, MigrateInstanceCommand):
            return self._migrate_instance(command)
        raise TypeError(f"Unsupported command: {type(command).__name__}")

    def _migrate_instance(self, command: MigrateInstanceCommand) -> dict[str, Any]:
        from palm.common.persistence.instance_migration import migrate_instance

        return migrate_instance(
            self._app.repository(),
            self._app.instance_manager,
            instance_id=command.instance_id,
            target_revision=command.target_revision,
            dry_run=command.dry_run,
        )

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
        pattern_projections: dict[str, Projection],
        resource_invocations: ResourceInvocationProjection,
        job_board: JobStatusBoardProjection,
        instance_manager: InstanceManager,
    ) -> None:
        self._app = app
        self._instances = instances
        self._pattern_projections = pattern_projections
        self._resource_invocations = resource_invocations
        self._job_board = job_board
        self._instance_manager = instance_manager

    def ask(self, query: Any) -> Any:
        for contributor in iter_cqrs_contributors():
            if contributor.handle_query is None:
                continue
            if isinstance(query, contributor.query_types):
                return contributor.handle_query(query, self)

        if isinstance(query, ListInstancesQuery):
            return self._instances.list_instances(query)
        if isinstance(query, GetInstanceStatusQuery):
            return self._instances.get_instance(query)
        if isinstance(query, ListInstanceSnapshotsQuery):
            return self._instance_manager.list_state_snapshots(query.instance_id)
        if isinstance(query, GetInstanceSnapshotQuery):
            return self._get_snapshot(query)
        if isinstance(query, ListFlowsQuery):
            return self._list_flows(query)
        if isinstance(query, GetFlowQuery):
            return self._get_flow(query)
        if isinstance(query, AnalyzeDefinitionImpactQuery):
            return self._analyze_definition_impact(query)
        if isinstance(query, ListProcessesQuery):
            return self._app.list_processes()
        if isinstance(query, GetProcessQuery):
            return self._get_process(query)
        if isinstance(query, GetJobStatusQuery):
            return self._get_job(query)
        if isinstance(query, GetJobContextQuery):
            return self._get_job_context(query)
        if isinstance(query, InspectInstanceQuery):
            return handle_inspect_instance(query, self)
        if isinstance(query, ListJobStatusQuery):
            return self._job_board.list_jobs(query)
        if isinstance(query, GetResourceInvocationsQuery):
            row = self._resource_invocations.get_invocations(query)
            return row.to_dict() if row is not None else None
        if isinstance(query, ListResourceInvocationsQuery):
            return [row.to_dict() for row in self._resource_invocations.list_invocations(query)]
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

    def _get_job_context(self, query: GetJobContextQuery) -> dict[str, Any]:
        try:
            job = self._app.runtime().get_job(query.job_id)
        except Exception:
            return {"found": False, "job_id": query.job_id}

        instance_id = instance_id_for_job(job)
        instance = None
        try:
            instance = self._instance_manager.get(instance_id)
        except InstanceNotFoundError:
            pass

        wizard_progress = None
        wizard_proj = self._pattern_projections.get("wizard")
        if wizard_proj is not None:
            progress = wizard_proj.get_progress(
                GetWizardProgressQuery(job_id=query.job_id, instance_id=instance_id)
            )
            wizard_progress = progress.to_dict() if progress is not None else None

        resource_row = self._resource_invocations.get_invocations(
            GetResourceInvocationsQuery(job_id=query.job_id, instance_id=instance_id)
        )
        resource_invocations = resource_row.to_dict() if resource_row is not None else None
        from palm.runtimes.cli.shared.job_inspect import inspect_job_json

        return build_job_context(
            job,
            pattern=inspect_job_json(job),
            instance=instance,
            wizard_progress=wizard_progress,
            resource_invocations=resource_invocations,
        )

    def _get_snapshot(self, query: GetInstanceSnapshotQuery) -> tuple[int, StateSnapshot] | None:
        try:
            snapshots = self._instance_manager.list_state_snapshots(query.instance_id)
        except InstanceNotFoundError:
            raise
        resolved = resolve_snapshot(snapshots, query.snapshot_id)
        if resolved is None:
            return None
        return resolved

    def _list_flows(self, query: ListFlowsQuery) -> list[FlowDefinition]:
        flows = self._app.list_flows()
        if query.pattern is not None:
            flows = [flow for flow in flows if flow.pattern == query.pattern]
        return flows

    def _get_flow(self, query: GetFlowQuery) -> FlowDefinition | None:
        try:
            return resolve_flow(
                self._app.repository(),
                query.flow_id,
                revision=query.revision,
            )
        except DefinitionNotFoundError:
            return None

    def _analyze_definition_impact(self, query: AnalyzeDefinitionImpactQuery) -> dict[str, Any]:
        from palm.common.persistence.definition_impact import analyze_definition_impact_or_raise

        repository = self._app.repository()
        instances = self._instance_manager.list_instances()
        return analyze_definition_impact_or_raise(
            repository,
            instances,
            flow_id=query.flow_id,
            target_revision=query.target_revision,
        )

    def _get_process(self, query: GetProcessQuery) -> ProcessDefinition | None:
        try:
            return resolve_process(self._app.repository(), query.process_id)
        except DefinitionNotFoundError:
            return None


def collect_cqrs_command_types() -> tuple[type, ...]:
    types: list[type] = [
        SubmitFlowCommand,
        SubmitProcessCommand,
        ProvideInputCommand,
        ResumeProcessCommand,
        PreparePlansCommand,
        SubmitPlansCommand,
        CancelJobCommand,
        MigrateInstanceCommand,
    ]
    for contributor in iter_cqrs_contributors():
        types.extend(contributor.command_types)
    return tuple(types)


def collect_cqrs_query_types() -> tuple[type, ...]:
    types: list[type] = [
        ListInstancesQuery,
        GetInstanceStatusQuery,
        ListInstanceSnapshotsQuery,
        GetInstanceSnapshotQuery,
        ListFlowsQuery,
        AnalyzeDefinitionImpactQuery,
        GetFlowQuery,
        ListProcessesQuery,
        GetProcessQuery,
        GetJobStatusQuery,
        GetJobContextQuery,
        InspectInstanceQuery,
        ListJobStatusQuery,
        GetResourceInvocationsQuery,
        ListResourceInvocationsQuery,
    ]
    for contributor in iter_cqrs_contributors():
        types.extend(contributor.query_types)
    return tuple(types)


def wire_command_bus(bus: CommandBus, app: PalmApp, router: RuntimeRouter) -> None:
    handler = PalmCommandHandlers(app, router)
    for command_type in collect_cqrs_command_types():
        bus.register(command_type, handler)


def wire_query_bus(
    bus: QueryBus,
    *,
    app: PalmApp,
    instances: InstanceIndexProjection,
    pattern_projections: dict[str, Projection],
    resource_invocations: ResourceInvocationProjection,
    job_board: JobStatusBoardProjection,
    instance_manager: InstanceManager,
) -> None:
    handler = HostQueryHandlers(
        app=app,
        instances=instances,
        pattern_projections=pattern_projections,
        resource_invocations=resource_invocations,
        job_board=job_board,
        instance_manager=instance_manager,
    )
    for query_type in collect_cqrs_query_types():
        bus.register(query_type, handler)
