"""Pure core tests for OrchestrationEngine contracts."""

from __future__ import annotations

import pytest

from palm.core.context import ContextEngine
from palm.core.event import EventEngine
from palm.core.exceptions import ConfigurationError
from palm.core.orchestration import (
    ExecutionContext,
    Job,
    JobRunner,
    JobStatus,
    OrchestrationEngine,
    OrchestrationEventType,
    RunResult,
)
from palm.core.orchestration.exceptions import JobNotFoundError, OrchestratorError
from tests.core.fakes import FakeInputCapable, TestState
from tests.core.fakes.mode import TestMode


def test_submit_succeeds_with_test_backend(orchestration_engine: OrchestrationEngine) -> None:
    job = orchestration_engine.submit(
        {"steps": 1, "final_status": "SUCCEEDED", "result": "ok"}
    )
    assert isinstance(job, Job)
    assert job.status == JobStatus.SUCCEEDED
    assert job.result == "ok"


def test_get_job_and_list_by_status(orchestration_engine: OrchestrationEngine) -> None:
    done = orchestration_engine.submit({"steps": 1, "final_status": "SUCCEEDED"})
    waiting = orchestration_engine.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})
    assert orchestration_engine.get_job(done.id) is done
    assert done in orchestration_engine.list_jobs(JobStatus.SUCCEEDED)
    assert waiting in orchestration_engine.list_jobs(JobStatus.WAITING_FOR_INPUT)


def test_unknown_job_raises(orchestration_engine: OrchestrationEngine) -> None:
    with pytest.raises(JobNotFoundError):
        orchestration_engine.get_job("missing")


def test_max_concurrent_jobs_enforced(orchestration_engine: OrchestrationEngine) -> None:
    orchestration_engine.max_concurrent_jobs = 2
    orchestration_engine.submit({"steps": 1})
    orchestration_engine.submit({"steps": 1})
    with pytest.raises(OrchestratorError, match="Maximum concurrent"):
        orchestration_engine.submit({"steps": 1})


def test_waiting_job_survives_engine_stop(orchestration_engine: OrchestrationEngine) -> None:
    job = orchestration_engine.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})
    assert job.status == JobStatus.WAITING_FOR_INPUT
    orchestration_engine.stop()
    assert orchestration_engine.get_job(job.id).status == JobStatus.WAITING_FOR_INPUT


class _WaitThenSucceedRunner(JobRunner):
    def run(self, ctx: ExecutionContext, *, budget: int | None = None) -> RunResult:
        if ctx.job.status == JobStatus.PENDING:
            return RunResult(status=JobStatus.WAITING_FOR_INPUT)
        if ctx.job.status == JobStatus.WAITING_FOR_INPUT:
            if ctx.job.state.has("__input__"):
                return RunResult(status=JobStatus.SUCCEEDED)
            return RunResult(status=JobStatus.WAITING_FOR_INPUT)
        return RunResult(status=JobStatus.SUCCEEDED)


def test_deliver_input_resumes_input_capable_job() -> None:
    executable = FakeInputCapable(step="name")
    engine = OrchestrationEngine()
    engine.initialize(mode=TestMode(runner=_WaitThenSucceedRunner()))
    engine.start()

    job = engine.submit(executable)
    assert job.status == JobStatus.WAITING_FOR_INPUT

    slug = engine.deliver_input(job.id, "Ada")
    assert slug == "name"
    assert executable.values == ["Ada"]
    assert job.status == JobStatus.SUCCEEDED

    engine.stop()
    engine.shutdown()


def test_deliver_input_rejects_non_capable_executable(orchestration_engine: OrchestrationEngine) -> None:
    job = orchestration_engine.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})
    with pytest.raises(TypeError, match="does not accept delivered input"):
        orchestration_engine.deliver_input(job.id, "x")


def test_waiting_job_resumes_via_provide_input(orchestration_engine: OrchestrationEngine) -> None:
    job = orchestration_engine.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})
    assert job.status == JobStatus.WAITING_FOR_INPUT
    orchestration_engine.provide_input(job.id, "answer", 42)
    assert job.status == JobStatus.SUCCEEDED
    assert job.state.get("answer") == 42


class _StatusOnlyRunner(JobRunner):
    """Runner that returns a result without mutating the job."""

    def __init__(self, status: JobStatus, *, result: object = None) -> None:
        self._status = status
        self._result = result

    def run(self, ctx: ExecutionContext, *, budget: int | None = None) -> RunResult:
        assert ctx.job.status == JobStatus.PENDING
        return RunResult(status=self._status, result=self._result)


def test_apply_result_is_lifecycle_authority() -> None:
    engine = OrchestrationEngine()
    engine.initialize(mode=TestMode(backend=_StatusOnlyRunner(JobStatus.SUCCEEDED, result="ok")))
    engine.start()
    job = engine.submit({"steps": 99})
    assert job.status == JobStatus.SUCCEEDED
    assert job.result == "ok"
    engine.stop()
    engine.shutdown()


def test_unconfigured_engine_requires_mode() -> None:
    engine = OrchestrationEngine()
    engine.start()
    with pytest.raises(ConfigurationError, match="requires initialize"):
        engine.submit({"steps": 1, "final_status": "SUCCEEDED"})


def test_orchestration_events_via_event_engine(
    event_engine: EventEngine,
    test_mode: TestMode,
) -> None:
    events: list[str] = []
    event_engine.subscribe("*", lambda e: events.append(e.type))

    engine = OrchestrationEngine()
    engine.initialize(mode=test_mode, event_engine=event_engine)
    engine.start()
    job = engine.submit({"steps": 1, "final_status": "SUCCEEDED"})
    engine.stop()
    engine.shutdown()

    assert OrchestrationEventType.ENGINE_STARTED in events
    assert OrchestrationEventType.JOB_SUBMITTED in events
    assert OrchestrationEventType.JOB_STATUS_CHANGED in events
    assert OrchestrationEventType.JOB_COMPLETED in events
    assert job.status == JobStatus.SUCCEEDED


def test_context_engine_binds_job_state(
    context_engine: ContextEngine,
    test_mode: TestMode,
) -> None:
    engine = OrchestrationEngine()
    engine.initialize(mode=test_mode, context_engine=context_engine)
    engine.start()

    state = TestState({"seed": 1})
    job = engine.submit({"steps": 1, "final_status": "SUCCEEDED"}, state=state)
    assert context_engine.current_state is state
    assert context_engine.get("job_id") == job.id
    engine.stop()
    engine.shutdown()