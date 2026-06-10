"""
CLI session context — thin delegate over :class:`~palm.app.app.PalmApp`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.app.app import PalmApp
from palm.app.settings import PalmSettings
from palm.common.exceptions import InstanceNotFoundError
from palm.common.managers import InstanceManager, InstanceSummary
from palm.core.orchestration import Job
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.instances import ProcessInstance, StateSnapshot


@dataclass
class CliContext:
    """Shared state for one-shot commands and the REPL."""

    app: PalmApp
    console: Any
    active_instance_id: str | None = None
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
        return self.app.list_instance_summaries()

    def list_instance_snapshots(self, instance_id: str) -> list[StateSnapshot]:
        return self.app.list_instance_snapshots(instance_id)

    def resolve_job_id(self, instance_or_job_id: str) -> str:
        """Map instance id to live job id, resuming from storage if needed."""
        if instance_or_job_id in self._instance_to_job:
            return self._instance_to_job[instance_or_job_id]

        try:
            inst = self.app.get_instance(instance_or_job_id)
        except InstanceNotFoundError:
            return instance_or_job_id

        job_id = inst.job_id
        try:
            self.app.get_job(job_id)
        except JobNotFoundError:
            job = self.app.resume_process(inst.instance_id)
            job_id = job.id
        self.set_active(inst.instance_id, job_id)
        return job_id

    def get_instance(self, ref: str) -> ProcessInstance:
        try:
            return self.app.get_instance(ref)
        except InstanceNotFoundError:
            pass
        for summary in self.list_instance_summaries():
            if summary.flow_name == ref or summary.process_name == ref:
                return self.app.get_instance(summary.instance_id)
        raise InstanceNotFoundError(ref)

    def job_for_instance(self, instance_id: str) -> Job:
        job_id = self.resolve_job_id(instance_id)
        return self.app.get_job(job_id)