"""Tests for DriveObservabilityHook middleware."""

from __future__ import annotations

from palm.common.runtimes.hooks import DriveObservabilityHook
from palm.core.orchestration import JobStatus, OrchestrationEngine
from tests.core.fakes.mode import TestMode


def test_drive_observability_hook_records_slices() -> None:
    hook = DriveObservabilityHook()
    engine = OrchestrationEngine()
    engine.initialize(scheduler=TestMode(), hooks=[hook])
    engine.start()

    job = engine.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})
    assert job.status == JobStatus.WAITING_FOR_INPUT
    assert hook.drive_count(job.id) == 1

    engine.provide_input(job.id, "key", "value")
    engine.resume_job(job.id)
    assert hook.drive_count(job.id) == 2
    assert len(hook.slices) == 2
    assert hook.slices[0].duration_ms >= 0

    engine.stop()
    engine.shutdown()


def test_observability_start_option_records_drives() -> None:
    from palm.runtimes.embedded import EmbeddedRuntime

    rt = EmbeddedRuntime()
    rt.start(observability=True)
    try:
        job = rt.submit_wizard(steps=1)
        hooks = [h for h in rt.orchestration._hooks if isinstance(h, DriveObservabilityHook)]
        assert len(hooks) == 1
        assert hooks[0].drive_count(job.id) >= 1
    finally:
        rt.stop()
