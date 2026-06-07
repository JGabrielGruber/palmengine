"""Tests for orchestration JobHook middleware."""

from __future__ import annotations

from palm.core.orchestration import JobStatus, OrchestrationEngine
from palm.core.orchestration.hooks import JobHookAdapter
from palm.core.orchestration.run_result import RunResult
from tests.core.fakes.mode import TestMode


class _RecordingHook(JobHookAdapter):
    def __init__(self) -> None:
        self.submitted: list[str] = []
        self.statuses: list[str] = []

    def on_job_submitted(self, engine: OrchestrationEngine, job) -> None:
        self.submitted.append(job.id)

    def on_job_status_changed(self, engine, job, result: RunResult | None = None) -> None:
        self.statuses.append(job.status.value)


def test_job_hooks_receive_submit_and_status_events() -> None:
    hook = _RecordingHook()
    engine = OrchestrationEngine()
    engine.initialize(mode=TestMode(), hooks=[hook])
    engine.start()

    job = engine.submit({"steps": 1, "final_status": "SUCCEEDED"})
    engine.stop()
    engine.shutdown()

    assert job.id in hook.submitted
    assert JobStatus.SUCCEEDED.value in hook.statuses