"""
Standalone server CQRS wiring — command/query buses without ApplicationHost.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.command import (
    CancelJobCommand,
    Command,
    PreparePlansCommand,
    ProvideInputCommand,
    ResumeProcessCommand,
    SubmitFlowCommand,
    SubmitPlansCommand,
    SubmitProcessCommand,
)
from palm.common.cqrs.instance_inspect import handle_inspect_instance
from palm.common.cqrs.query import (
    GetFlowQuery,
    GetInstanceSnapshotQuery,
    GetInstanceStatusQuery,
    GetJobContextQuery,
    GetJobStatusQuery,
    GetProcessQuery,
    InspectInstanceQuery,
    ListFlowsQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
    ListProcessesQuery,
    Query,
)
from palm.common.cqrs.resolvers import resolve_flow, resolve_process, resolve_snapshot
from palm.common.exceptions import DefinitionNotFoundError, InstanceNotFoundError, PlanNotFoundError
from palm.common.job_context import build_job_context, instance_id_for_job
from palm.common.patterns._registry import iter_cqrs_contributors
from palm.common.plans import PlanRegistry
from palm.common.runtimes.server.plans import prepare_flow_from_body, prepare_process_from_body
from palm.core.orchestration.exceptions import JobNotFoundError

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime


class StandaloneCommandHandlers:
    """Dispatch write operations directly through a hosting runtime."""

    def __init__(self, runtime: BaseRuntime, *, plan_registry: PlanRegistry) -> None:
        self._runtime = runtime
        self._plan_registry = plan_registry

    def handle(self, command: Command) -> Any:
        for contributor in iter_cqrs_contributors():
            if contributor.handle_command is None:
                continue
            if isinstance(command, contributor.command_types):
                return contributor.handle_command(command, self)

        if isinstance(command, SubmitFlowCommand):
            return self._submit_flow(command)
        if isinstance(command, SubmitProcessCommand):
            return self._submit_process(command)
        if isinstance(command, ProvideInputCommand):
            return self._runtime.provide_input(command.job_id, command.value)
        if isinstance(command, ResumeProcessCommand):
            return self._runtime.resume_process(command.instance_id)
        if isinstance(command, PreparePlansCommand):
            return self._prepare_plans(command)
        if isinstance(command, SubmitPlansCommand):
            return self._submit_plans(command)
        if isinstance(command, CancelJobCommand):
            return self._cancel_job(command)
        raise TypeError(f"Unsupported command: {type(command).__name__}")

    def _cancel_job(self, command: CancelJobCommand) -> dict[str, Any]:
        try:
            cancelled = self._runtime.cancel_job(command.job_id)
        except JobNotFoundError:
            return {"found": False, "job_id": command.job_id}
        job = self._runtime.get_job(command.job_id)
        return {
            "found": True,
            "job_id": command.job_id,
            "cancelled": cancelled,
            "status": job.status.value,
        }

    def _submit_flow(self, command: SubmitFlowCommand) -> Any:
        if isinstance(command.flow, dict):
            body = dict(command.flow)
            if command.job_id is not None:
                body.setdefault("job_id", command.job_id)
            plan = prepare_flow_from_body(self._runtime, body)
            return self._runtime.executor.submit_plan(plan)
        return self._runtime.submit_flow(
            command.flow,
            by_id=command.by_id,
            job_id=command.job_id,
            state=command.state,
            metadata=command.metadata,
        )

    def _submit_process(self, command: SubmitProcessCommand) -> Any:
        if isinstance(command.process, dict):
            body = dict(command.process)
            if command.job_id is not None:
                body.setdefault("job_id", command.job_id)
            bundle = prepare_process_from_body(self._runtime, body)
            jobs = self._runtime.executor.submit_plans(bundle.plans)
            return jobs[0] if len(jobs) == 1 else jobs
        return self._runtime.submit_process(
            command.process,
            by_id=command.by_id,
            job_id=command.job_id,
            state=command.state,
            metadata=command.metadata,
        )

    def _prepare_plans(self, command: PreparePlansCommand) -> dict[str, Any]:
        body = command.body
        if "process" in body or "process_name" in body:
            bundle = prepare_process_from_body(self._runtime, body)
            stored = [self._store_plan(plan) for plan in bundle.plans]
        else:
            plan = prepare_flow_from_body(self._runtime, body)
            stored = [self._store_plan(plan)]
        return {"plans": [self._plan_registry.summary(item) for item in stored]}

    def _submit_plans(self, command: SubmitPlansCommand) -> dict[str, Any]:
        jobs = []
        for plan_id in command.plan_ids:
            try:
                plan = self._plan_registry.consume(plan_id)
            except PlanNotFoundError as exc:
                raise exc
            jobs.append(self._runtime.executor.submit_plan(plan))
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

    def _store_plan(self, plan: Any) -> Any:
        from palm.common.runtimes.server.middleware import current_principal_id

        return self._plan_registry.store(plan, principal_id=current_principal_id(self._runtime))


class StandaloneQueryHandlers:
    """Serve reads from the authoritative runtime when no host projections exist."""

    def __init__(self, runtime: BaseRuntime) -> None:
        self._runtime = runtime
        self._pattern_projections: dict[str, Any] = {}

    def ask(self, query: Query) -> Any:
        for contributor in iter_cqrs_contributors():
            if contributor.handle_query is None:
                continue
            if isinstance(query, contributor.query_types):
                return contributor.handle_query(query, self)

        if isinstance(query, GetJobStatusQuery):
            return self._get_job(query)
        if isinstance(query, GetJobContextQuery):
            return self._get_job_context(query)
        if isinstance(query, InspectInstanceQuery):
            return handle_inspect_instance(query, self)
        if isinstance(query, ListJobStatusQuery):
            return self._list_jobs(query)
        if isinstance(query, ListInstancesQuery):
            return self._list_instances(query)
        if isinstance(query, GetInstanceStatusQuery):
            return self._get_instance(query)
        if isinstance(query, ListInstanceSnapshotsQuery):
            return self._list_snapshots(query.instance_id)
        if isinstance(query, GetInstanceSnapshotQuery):
            return self._get_snapshot(query)
        if isinstance(query, ListFlowsQuery):
            return self._list_flows(query)
        if isinstance(query, GetFlowQuery):
            return self._get_flow(query)
        if isinstance(query, ListProcessesQuery):
            return self._list_processes()
        if isinstance(query, GetProcessQuery):
            return self._get_process(query)
        raise TypeError(f"Unsupported query: {type(query).__name__}")

    def _get_job(self, query: GetJobStatusQuery) -> dict[str, Any]:
        try:
            job = self._runtime.get_job(query.job_id)
        except JobNotFoundError:
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
        step = _safe_wizard_step(self._runtime, query.job_id)
        if step is not None:
            payload["step"] = step
        return payload

    def _get_job_context(self, query: GetJobContextQuery) -> dict[str, Any]:
        try:
            job = self._runtime.get_job(query.job_id)
        except JobNotFoundError:
            return {"found": False, "job_id": query.job_id}

        instance_id = instance_id_for_job(job)
        instance = None
        try:
            instance = self._runtime.instance_manager.get(instance_id)
        except InstanceNotFoundError:
            pass

        wizard_progress = self._wizard_progress(
            instance_id=instance_id,
            job_id=query.job_id,
        )
        from palm.common.job_inspection import inspect_job_json

        return build_job_context(
            job,
            pattern=inspect_job_json(job),
            instance=instance,
            wizard_progress=wizard_progress,
        )

    def _list_jobs(self, query: ListJobStatusQuery) -> list[dict[str, Any]]:
        jobs = self._runtime.orchestration.list_jobs()
        rows = [
            {
                "job_id": job.id,
                "status": job.status.value,
                "metadata": job.metadata,
            }
            for job in jobs
        ]
        if query.status is not None:
            rows = [row for row in rows if row["status"] == query.status]
        if query.limit is not None:
            rows = rows[: query.limit]
        return rows

    def _list_instances(self, query: ListInstancesQuery) -> list[dict[str, Any]]:
        summaries = self._runtime.instance_manager.list_summaries()
        rows = [
            {
                "instance_id": summary.instance_id,
                "job_id": summary.job_id,
                "status": summary.status,
                "flow_name": summary.flow_name,
                "process_name": summary.process_name,
            }
            for summary in summaries
        ]
        if query.status is not None:
            rows = [row for row in rows if row["status"] == query.status]
        if query.flow_name is not None:
            rows = [row for row in rows if row.get("flow_name") == query.flow_name]
        if not query.include_terminal:
            rows = [
                row for row in rows if row["status"] not in {"SUCCEEDED", "FAILED", "CANCELLED"}
            ]
        if query.limit is not None:
            rows = rows[: query.limit]
        return rows

    def _get_instance(self, query: GetInstanceStatusQuery) -> dict[str, Any] | None:
        try:
            instance = self._runtime.get_instance(query.instance_id)
        except Exception:
            return None
        return {
            "instance_id": instance.instance_id,
            "job_id": instance.job_id,
            "status": instance.status,
            "flow_name": instance.flow_name,
            "process_name": instance.process_name,
            "current_step_slug": instance.current_step_slug,
        }

    def _list_snapshots(self, instance_id: str) -> list[Any]:
        try:
            return self._runtime.instance_manager.list_state_snapshots(instance_id)
        except InstanceNotFoundError as exc:
            raise exc

    def _get_snapshot(self, query: GetInstanceSnapshotQuery) -> Any:
        snapshots = self._list_snapshots(query.instance_id)
        resolved = resolve_snapshot(snapshots, query.snapshot_id)
        if resolved is None:
            return None
        return resolved

    def _list_flows(self, query: ListFlowsQuery) -> list[Any]:
        flows = self._runtime.repository.list_flows()
        if query.pattern is not None:
            flows = [flow for flow in flows if flow.pattern == query.pattern]
        return flows

    def _get_flow(self, query: GetFlowQuery) -> Any:
        try:
            return resolve_flow(
                self._runtime.repository,
                query.flow_id,
                revision=query.revision,
            )
        except DefinitionNotFoundError:
            return None

    def _list_processes(self) -> list[Any]:
        return self._runtime.repository.list_processes()

    def _get_process(self, query: GetProcessQuery) -> Any:
        try:
            return resolve_process(self._runtime.repository, query.process_id)
        except DefinitionNotFoundError:
            return None

    def _wizard_progress(
        self,
        *,
        instance_id: str | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any] | None:
        resolved_job_id = job_id
        if resolved_job_id is None and instance_id is not None:
            instance = self._get_instance(GetInstanceStatusQuery(instance_id=instance_id))
            if instance is not None:
                resolved_job_id = str(instance.get("job_id") or instance_id)
        if resolved_job_id is None:
            return None
        try:
            job = self._runtime.get_job(resolved_job_id)
        except JobNotFoundError:
            return None
        return {
            "job_id": resolved_job_id,
            "instance_id": instance_id or instance_id_for_job(job),
            "status": job.status.value,
            "step": _safe_wizard_step(self._runtime, resolved_job_id),
            "answers": _safe_wizard_answers(self._runtime, resolved_job_id),
        }


def wire_standalone_buses(
    command_bus: CommandBus,
    query_bus: QueryBus,
    runtime: BaseRuntime,
    *,
    plan_registry: PlanRegistry,
) -> None:
    commands = StandaloneCommandHandlers(runtime, plan_registry=plan_registry)
    queries = StandaloneQueryHandlers(runtime)
    from palm.common.cqrs.catalog import collect_cqrs_command_types, collect_cqrs_query_types

    command_types = list(collect_cqrs_command_types(mode="standalone"))
    query_types = list(collect_cqrs_query_types(mode="standalone"))
    for command_type in command_types:
        command_bus.register(command_type, commands)
    for query_type in query_types:
        query_bus.register(query_type, queries)


def _safe_wizard_step(runtime: BaseRuntime, job_id: str) -> str | None:
    try:
        return runtime.current_wizard_step(job_id)
    except TypeError:
        return None


def _safe_wizard_answers(runtime: BaseRuntime, job_id: str) -> dict[str, Any]:
    # Non-wizard (e.g. etl) instances are not StepInspectable; inspect must not crash.
    try:
        return runtime.wizard_answers(job_id)
    except TypeError:
        return {}
