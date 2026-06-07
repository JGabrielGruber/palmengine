"""
Definition executor — submits flows and processes via a runtime.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, overload

from palm.core.orchestration import Job
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.executions.build_context import PatternBuildContext
from palm.executions.exceptions import (
    DefinitionBuildError,
    DefinitionNotFoundError,
    InstanceResumeError,
)
from palm.executions.flow_submission import prepare_flow_submission, prepare_resume_submission
from palm.executions.plan import ExecutionPlan
from palm.executions.process_submission import ProcessPlan, prepare_process_plans
from palm.executions.instance_events import is_resumable_status
from palm.executions.instance_repository import InstanceRepository
from palm.executions.repository import DefinitionRepository

if TYPE_CHECKING:
    from palm.core.context import BaseState
    from palm.runtimes.host import RuntimeHost


class DefinitionExecutor:
    """
    Bridges declarative definitions to orchestration jobs.

    Accepts in-memory definitions, or resolves names/ids through a
    ``DefinitionRepository``. Instance persistence is handled by
    :class:`~palm.executions.hooks.InstancePersistenceHook` on the orchestration engine.
    """

    def __init__(
        self,
        runtime: RuntimeHost,
        repository: DefinitionRepository | None = None,
        instances: InstanceRepository | None = None,
    ) -> None:
        self._runtime = runtime
        self._repository = repository
        self._instances = instances

    @property
    def repository(self) -> DefinitionRepository | None:
        return self._repository

    @property
    def instances(self) -> InstanceRepository | None:
        return self._instances

    @overload
    def submit_flow(
        self,
        flow: FlowDefinition,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job: ...

    @overload
    def submit_flow(
        self,
        flow: str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job: ...

    def submit_flow(
        self,
        flow: FlowDefinition | str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """Build a pattern from a flow (or repository ref) and submit a job."""
        return self.submit_plan(
            self.prepare_flow_plan(
                flow,
                by_id=by_id,
                job_id=job_id,
                instance_id=instance_id,
                state=state,
                metadata=metadata,
            )
        )

    @overload
    def prepare_flow_plan(
        self,
        flow: FlowDefinition,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionPlan: ...

    @overload
    def prepare_flow_plan(
        self,
        flow: str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionPlan: ...

    def prepare_flow_plan(
        self,
        flow: FlowDefinition | str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionPlan:
        """Prepare an :class:`~palm.executions.plan.ExecutionPlan` without submitting."""
        resolved = self._resolve_flow(flow, by_id=by_id)
        self._require_runtime()
        submission = prepare_flow_submission(
            resolved,
            state=state,
            metadata=metadata,
            instances=self._instances,
            build_ctx=self._build_context(),
            instance_id=instance_id,
        )
        return submission.to_plan(job_id=job_id)

    def submit_plan(self, plan: ExecutionPlan) -> Job:
        """Submit a prepared :class:`~palm.executions.plan.ExecutionPlan` to orchestration."""
        self._require_runtime()
        return plan.submit_to(self._runtime.orchestration)

    def submit_plans(self, plans: Iterable[ExecutionPlan]) -> list[Job]:
        """Submit multiple prepared plans in order."""
        return [self.submit_plan(plan) for plan in plans]

    def resume_process(self, instance_id: str) -> Job:
        """
        Resume a persisted process instance in this runtime.

        Rebuilds the flow executable, restores state (and wizard position), and
        re-submits to orchestration using the stored ``job_id`` when free.
        """
        self._require_runtime()
        repo = self._instances
        if repo is None:
            raise InstanceResumeError("InstanceRepository is not configured")

        instance = repo.get(instance_id)
        if not is_resumable_status(instance.status):
            raise InstanceResumeError(
                f"Instance {instance_id!r} is not resumable (status={instance.status})"
            )

        submission = prepare_resume_submission(instance, build_ctx=self._build_context())

        try:
            existing = self._runtime.orchestration.get_job(instance.job_id)
            if existing.is_live:
                raise InstanceResumeError(
                    f"Job {instance.job_id!r} is already active in this runtime"
                )
        except JobNotFoundError:
            pass

        return self.submit_plan(submission.to_plan(job_id=instance.job_id))

    @overload
    def submit_process(
        self,
        process: ProcessDefinition,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]: ...

    @overload
    def submit_process(
        self,
        process: str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]: ...

    def submit_process(
        self,
        process: ProcessDefinition | str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]:
        """Submit one job per flow on a process (or repository ref)."""
        return self.submit_plans(
            self.prepare_process_plan(
                process,
                by_id=by_id,
                job_id=job_id,
                instance_id=instance_id,
                state=state,
                metadata=metadata,
            ).plans
        )

    @overload
    def prepare_process_plan(
        self,
        process: ProcessDefinition,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProcessPlan: ...

    @overload
    def prepare_process_plan(
        self,
        process: str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProcessPlan: ...

    def prepare_process_plan(
        self,
        process: ProcessDefinition | str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProcessPlan:
        """Prepare a :class:`~palm.executions.process_submission.ProcessPlan` without submitting."""
        resolved = self._resolve_process(process, by_id=by_id)
        if not resolved.flows:
            raise DefinitionBuildError(f"Process {resolved.name!r} defines no flows")
        self._require_runtime()
        return prepare_process_plans(
            resolved,
            state=state,
            metadata=metadata,
            instances=self._instances,
            build_ctx=self._build_context(),
            job_id=job_id,
            instance_id=instance_id,
        )

    def submit_flow_by_name(
        self,
        name: str,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        return self.submit_flow(
            name,
            by_id=False,
            job_id=job_id,
            instance_id=instance_id,
            state=state,
            metadata=metadata,
        )

    def submit_flow_by_id(
        self,
        definition_id: str,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        return self.submit_flow(
            definition_id,
            by_id=True,
            job_id=job_id,
            instance_id=instance_id,
            state=state,
            metadata=metadata,
        )

    def submit_process_by_name(
        self,
        name: str,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]:
        return self.submit_process(
            name,
            by_id=False,
            job_id=job_id,
            instance_id=instance_id,
            state=state,
            metadata=metadata,
        )

    def submit_process_by_id(
        self,
        definition_id: str,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]:
        return self.submit_process(
            definition_id,
            by_id=True,
            job_id=job_id,
            instance_id=instance_id,
            state=state,
            metadata=metadata,
        )

    def persist_job(self, job: Job) -> None:
        """Manually flush the latest job snapshot (usually handled by :class:`InstancePersistenceHook`)."""
        if self._instances is None:
            return
        iid = job.metadata.get("instance_id")
        if not iid:
            return
        self._instances.update(job, instance_id=str(iid))

    def _resolve_flow(self, flow: FlowDefinition | str, *, by_id: bool) -> FlowDefinition:
        if isinstance(flow, FlowDefinition):
            return flow
        repo = self._repository
        if repo is None:
            raise DefinitionBuildError(
                "Cannot resolve flow by reference without a DefinitionRepository"
            )
        try:
            return repo.get_flow(flow, by_id=by_id)
        except DefinitionNotFoundError as exc:
            raise DefinitionBuildError(str(exc)) from exc

    def _resolve_process(
        self, process: ProcessDefinition | str, *, by_id: bool
    ) -> ProcessDefinition:
        if isinstance(process, ProcessDefinition):
            return process
        repo = self._repository
        if repo is None:
            raise DefinitionBuildError(
                "Cannot resolve process by reference without a DefinitionRepository"
            )
        try:
            return repo.get_process(process, by_id=by_id)
        except DefinitionNotFoundError as exc:
            raise DefinitionBuildError(str(exc)) from exc

    def _build_context(self) -> PatternBuildContext:
        return PatternBuildContext(
            event_engine=self._runtime.event,
            resource_engine=getattr(self._runtime, "resource", None),
        )

    def _require_runtime(self) -> None:
        if not self._runtime.is_started:
            raise RuntimeError(
                "Runtime host is not started; call start() before submitting definitions"
            )


ProcessExecutor = DefinitionExecutor
