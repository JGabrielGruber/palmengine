"""
CLI session context — PalmApp, console, and active instance tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.app.app import PalmApp
from palm.common.exceptions import InstanceNotFoundError
from palm.core.orchestration import Job
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.instances import ProcessInstance


@dataclass
class CliContext:
    """Shared state for one-shot commands and the REPL."""

    app: PalmApp
    console: Any
    active_instance_id: str | None = None
    _instance_to_job: dict[str, str] = field(default_factory=dict)

    def set_active(self, instance_id: str, job_id: str) -> None:
        self.active_instance_id = instance_id
        self._instance_to_job[instance_id] = job_id

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
        for inst in self.app.list_instances():
            if inst.flow_name == ref or inst.process_name == ref:
                return inst
        raise InstanceNotFoundError(ref)

    def job_for_instance(self, instance_id: str) -> Job:
        job_id = self.resolve_job_id(instance_id)
        return self.app.get_job(job_id)