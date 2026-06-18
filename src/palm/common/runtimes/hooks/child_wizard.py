"""Auto-resume parent wizards when a correlated nested child job completes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.wizard_child_wait import resume_parent_after_child
from palm.core.orchestration.hooks import JobHookAdapter
from palm.core.orchestration.job import JobStatus

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job
    from palm.core.orchestration.run_result import RunResult


class ChildWizardCompletionHook(JobHookAdapter):
    """Resume parent wizard jobs waiting on a nested child flow."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime

    def on_job_status_changed(
        self,
        engine: OrchestrationEngine,
        job: Job,
        result: RunResult | None = None,
    ) -> None:
        if job.status != JobStatus.SUCCEEDED:
            return
        resume_parent_after_child(self._runtime, job)