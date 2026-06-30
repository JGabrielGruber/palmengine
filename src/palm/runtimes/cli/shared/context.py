"""
CLI session context — ApplicationHost-backed commands and queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from palm.app.settings import PalmSettings
from palm.common.cqrs.adapters import read_model_to_summary
from palm.common.exceptions import InstanceNotFoundError
from palm.common.managers import InstanceManager, InstanceSummary
from palm.common.services.session import ReplSession
from palm.core.orchestration import Job
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.definitions.resource import ResourceDefinition
from palm.instances import ProcessInstance, StateSnapshot
from palm.runtimes.cli.shared.instances import resolve_instance_id as _resolve_instance_id

if TYPE_CHECKING:
    from palm.app.app import PalmApp
    from palm.app.host.application_host import ApplicationHost


@dataclass
class CliContext:
    """
    Shared state for one-shot commands and the REPL.

    All CLI operations route through :class:`~palm.app.host.ApplicationHost`
    for CQRS command dispatch, query serving, and coordinated recovery.
    """

    host: ApplicationHost
    console: Any
    active_instance_id: str | None = None
    output_format: str = "table"
    _instance_to_job: dict[str, str] = field(default_factory=dict)
    _repl_session: ReplSession | None = field(default=None, repr=False)

    @property
    def app(self) -> PalmApp:
        """Infrastructure layer — definitions, storage, runtime registry."""
        return self.host.app

    @property
    def settings(self) -> PalmSettings:
        return self.app.settings

    @property
    def instance_manager(self) -> InstanceManager:
        return self.app.instance_manager

    @property
    def repl(self) -> ReplSession:
        """Stateful REPL handle — tracks the active instance across commands."""
        if self._repl_session is None:
            self._repl_session = ReplSession(self.host.execution)
        return self._repl_session

    def is_runtime_started(self) -> bool:
        return self.host.is_started and bool(self.host.running_runtimes())

    def running_runtime_names(self) -> list[str]:
        return self.host.running_runtimes()

    def set_active(self, instance_id: str, job_id: str) -> None:
        self.active_instance_id = instance_id
        self._instance_to_job[instance_id] = job_id
        self.instance_manager.mark_active(instance_id)
        self.repl.activate(instance_id)

    def list_instance_summaries(self) -> list[InstanceSummary]:
        views = self.host.list_instance_views(include_terminal=True)
        return [read_model_to_summary(view) for view in views]

    def resolve_instance_id(self, ref: str) -> str:
        return _resolve_instance_id(self, ref)

    def get_instance(self, ref: str) -> ProcessInstance:
        instance_id = self.resolve_instance_id(ref)
        return self.instance_manager.get(instance_id)

    def get_instance_status_view(self, ref: str):
        instance_id = self.resolve_instance_id(ref)
        return self.host.get_instance_view(instance_id)

    def list_instance_snapshots(self, instance_id: str) -> list[StateSnapshot]:
        resolved = self.resolve_instance_id(instance_id)
        return self.host.list_instance_snapshots(resolved)

    def resolve_flow(self, ref: str) -> FlowDefinition:
        return self.app.resolve_flow(ref)

    def resolve_process(self, ref: str) -> ProcessDefinition:
        return self.app.resolve_process(ref)

    def resolve_resource(self, ref: str) -> ResourceDefinition:
        return self.app.resolve_resource(ref)

    def submit_flow(
        self,
        ref: FlowDefinition | str,
        *,
        job_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        return self.host.submit_flow(ref, job_id=job_id, metadata=metadata)

    def submit_process(
        self,
        ref: ProcessDefinition | str,
        *,
        job_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job | list[Job]:
        return self.host.submit_process(ref, job_id=job_id, metadata=metadata)

    def provide_input(self, job_id: str, value: Any) -> str | None:
        return self.host.provide_input(job_id, value)

    def resume_process(self, instance_id: str) -> Job:
        return self.host.resume_process(instance_id)

    def get_job(self, job_id: str) -> Job:
        return self.app.get_job(job_id)

    def resume_job(self, job_id: str) -> None:
        self.app.resume_job(job_id)

    def persist_job(self, job: Job) -> None:
        self.app.persist_job(job)

    def resolve_job_id(self, instance_or_job_id: str) -> str:
        if instance_or_job_id in self._instance_to_job:
            return self._instance_to_job[instance_or_job_id]

        try:
            instance_id = self.resolve_instance_id(instance_or_job_id)
        except InstanceNotFoundError:
            return instance_or_job_id

        inst = self.instance_manager.get(instance_id)
        job_id = inst.job_id
        try:
            self.get_job(job_id)
        except JobNotFoundError:
            job = self.host.resume_process(inst.instance_id)
            job_id = job.id
        self.set_active(inst.instance_id, job_id)
        return job_id

    def job_for_instance(self, instance_id: str) -> Job:
        job_id = self.resolve_job_id(instance_id)
        return self.get_job(job_id)
