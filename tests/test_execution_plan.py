"""Tests for ExecutionPlan submission boundary."""

from __future__ import annotations

from palm.core.orchestration import JobStatus
from palm.definitions.flow import FlowDefinition
from palm.executions import ExecutionPlan, prepare_flow_submission
from palm.executions.build_context import PatternBuildContext
from palm.runtimes.embedded import EmbeddedRuntime


def test_flow_submission_to_plan_and_submit() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        flow = FlowDefinition(name="noop", pattern="wizard", options={"steps": 1})
        submission = prepare_flow_submission(
            flow,
            state=None,
            metadata=None,
            instances=rt.instances,
            build_ctx=PatternBuildContext(event_engine=rt.event),
        )
        plan = submission.to_plan(job_id="planned-job")
        assert isinstance(plan, ExecutionPlan)
        assert plan.job_id == "planned-job"
        assert plan.metadata["flow"] == "noop"

        job = rt.executor.submit_plan(plan)
        assert job.id == "planned-job"
        assert job.status == JobStatus.WAITING_FOR_INPUT
    finally:
        rt.stop()


def test_execution_plan_submit_to() -> None:
    from palm.states import BlackboardState

    from tests.core.fakes.backend import TestBackend

    rt = EmbeddedRuntime()
    rt.start(runner=TestBackend())
    try:
        plan = ExecutionPlan(
            executable={"steps": 1, "final_status": "SUCCEEDED", "result": "ok"},
            state=BlackboardState(),
            metadata={"source": "test"},
        )
        job = plan.submit_to(rt.orchestration)
        assert job.status == JobStatus.SUCCEEDED
        assert job.result == "ok"
    finally:
        rt.stop()