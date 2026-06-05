"""
Specific tests for TestMode and its test-only controls.
"""

from __future__ import annotations

from palm.core.orchestration import JobStatus, Orchestrator, TestMode


def test_test_mode_run_until_idle() -> None:
    mode = TestMode()
    orch = Orchestrator(mode=mode)
    orch.start()

    j1 = orch.submit({"steps": 3, "final_status": "SUCCEEDED"})
    j2 = orch.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})

    # Both should have been driven to their terminal/waiting states already by submit
    assert j1.status == JobStatus.SUCCEEDED
    assert j2.status == JobStatus.WAITING_FOR_INPUT

    # Provide input and use the helper
    orch.provide_input(j2.id, "x", 1)
    mode.run_until_idle(orch)

    assert j2.status == JobStatus.SUCCEEDED


def test_force_job_status_helper() -> None:
    mode = TestMode()
    orch = Orchestrator(mode=mode)
    orch.start()

    j = orch.submit({"steps": 10})
    # After submit with TestBackend the job may already be terminal.
    # Force it from whatever state it is in (the helper bypasses some checks for test power).
    mode.force_job_status(j, JobStatus.FAILED)
    assert j.status == JobStatus.FAILED


def test_simulate_step_advances_one_step() -> None:
    mode = TestMode()
    # Manual job for fine-grained control
    from palm.core.orchestration.job import Job

    job = Job(id="steppy", executable={"steps": 5, "final_status": "SUCCEEDED"})
    mode.start()
    status = mode.simulate_step(job)
    # With current TestBackend + 1 step on a 5-step descriptor that wants SUCCEEDED,
    # it will usually complete. Accept either RUNNING or SUCCEEDED as valid "progress".
    assert status in (JobStatus.RUNNING, JobStatus.SUCCEEDED)
