"""
CLI session context — ApplicationHost-backed queries with PalmApp commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from palm.app.app import PalmApp
from palm.app.settings import PalmSettings
from palm.common.cqrs.adapters import read_model_to_summary
from palm.common.cqrs.query import ListInstanceSnapshotsQuery, ListInstancesQuery
from palm.common.exceptions import InstanceNotFoundError
from palm.common.managers import InstanceManager, InstanceSummary
from palm.core.orchestration import Job
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.instances import ProcessInstance, StateSnapshot
from palm.runtimes.cli.shared.instances import resolve_instance_id as _resolve_instance_id

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost


@dataclass
class CliContext:
    """Shared state for one-shot commands and the REPL."""

    app: PalmApp
    console: Any
    host: ApplicationHost | None = None
    active_instance_id: str | None = None
    output_format: str = "table"
    _instance_to_job: dict[str, str] = field(default_factory=dict)

    @property
    def settings(self) -> PalmSettings:
        return self.app.settings

    @property
    def instance_manager(self) -> InstanceManager:
        return self.app.instance_manager

    def set_active(self, instance_id: str, job_id: str) -> None:
        self.active_instance_id = instance_id
        self._instance_to_job[instance_id] = job_id
        self.instance_manager.mark_active(instance_id)

    def list_instance_summaries(self) -> list[InstanceSummary]:
        """List instances via the host query bus when available."""
        if self._query_ready():
            views = self.host.list_instance_views(include_terminal=True)
            return [read_model_to_summary(view) for view in views]
        return self.instance_manager.list_summaries()

    def resolve_instance_id(self, ref: str) -> str:
        """Resolve exact id, unique prefix, or flow/process name to ``instance_id``."""
        return _resolve_instance_id(self, ref)

    def get_instance(self, ref: str) -> ProcessInstance:
        instance_id = self.resolve_instance_id(ref)
        return self.instance_manager.get(instance_id)

    def get_instance_status_view(self, ref: str):
        """Return the CQRS read model for an instance when the host is active."""
        if not self._query_ready():
            return None
        instance_id = self.resolve_instance_id(ref)
        return self.host.get_instance_view(instance_id)

    def list_instance_snapshots(self, instance_id: str) -> list[StateSnapshot]:
        resolved = self.resolve_instance_id(instance_id)
        if self._query_ready():
            return self.host.list_instance_snapshots(resolved)
        return self.instance_manager.list_state_snapshots(resolved)

    def resolve_job_id(self, instance_or_job_id: str) -> str:
        """Map instance id to live job id, resuming from storage if needed."""
        if instance_or_job_id in self._instance_to_job:
            return self._instance_to_job[instance_or_job_id]

        try:
            instance_id = self.resolve_instance_id(instance_or_job_id)
        except InstanceNotFoundError:
            return instance_or_job_id

        inst = self.instance_manager.get(instance_id)
        job_id = inst.job_id
        try:
            self.app.get_job(job_id)
        except JobNotFoundError:
            if self.host is not None and self.host.is_started:
                job = self.host.resume_process(inst.instance_id)
            else:
                job = self.app.resume_process(inst.instance_id)
            job_id = job.id
        self.set_active(inst.instance_id, job_id)
        return job_id

    def job_for_instance(self, instance_id: str) -> Job:
        job_id = self.resolve_job_id(instance_id)
        return self.app.get_job(job_id)

    def _query_ready(self) -> bool:
        return self.host is not None and self.host.is_started