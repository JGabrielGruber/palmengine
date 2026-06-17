"""Stamp execution correlation on job state and context engine before each drive."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.resource.observability import stamp_execution_context  # — hook layer
from palm.core.orchestration.hooks import JobHookAdapter

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job
    from palm.core.orchestration.run_result import RunResult


class JobExecutionContextHook(JobHookAdapter):
    """Expose job/instance identifiers to patterns and resource events during drive."""

    def on_before_drive(self, engine: OrchestrationEngine, job: Job) -> None:
        wizard_name = _wizard_name(job.metadata)
        stamp_execution_context(
            job.state,
            job_id=job.id,
            instance_id=_optional_str(job.metadata.get("instance_id")),
            flow=_optional_str(job.metadata.get("flow")),
            wizard=wizard_name,
            trace_id=_optional_str(job.metadata.get("trace_id")),
        )
        context_engine = engine.context_engine
        if context_engine is None or not context_engine.is_initialized:
            return
        frame = {
            "job_id": job.id,
            "instance_id": job.metadata.get("instance_id"),
            "flow": job.metadata.get("flow"),
            "wizard": wizard_name,
            "trace_id": job.metadata.get("trace_id"),
        }
        for key, value in frame.items():
            if value is not None:
                context_engine.set(key, value)

    def on_after_drive(
        self,
        engine: OrchestrationEngine,
        job: Job,
        result: RunResult,
    ) -> None:
        return None


def _wizard_name(metadata: dict[str, Any]) -> str | None:
    wizard_meta = metadata.get("wizard")
    if isinstance(wizard_meta, dict):
        name = wizard_meta.get("name")
        return str(name) if name is not None else None
    return None


def _optional_str(value: object) -> str | None:
    return str(value) if value is not None else None
