"""Tests for ExecutionPlan validation and PlanRegistry."""

from __future__ import annotations

import pytest

from palm.common import ExecutionPlan, PlanNotFoundError, PlanRegistry, PlanValidationError
from palm.common.plans import ProcessPlan
from palm.definitions import FlowDefinition, ProcessDefinition
from palm.runtimes.embedded import EmbeddedRuntime
from palm.states import BlackboardState


def test_execution_plan_validate_rejects_missing_executable() -> None:
    plan = ExecutionPlan(executable=None, state=BlackboardState(), metadata={})
    with pytest.raises(PlanValidationError, match="executable"):
        plan.validate()


def test_plan_registry_store_and_consume() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        plan = rt.executor.prepare_flow_plan(
            FlowDefinition(name="noop", pattern="wizard", options={"steps": 1}),
        )
    finally:
        rt.stop()

    registry = PlanRegistry()
    stored = registry.store(plan)
    assert stored.plan_id.startswith("plan-")
    consumed = registry.consume(stored.plan_id)
    assert consumed.metadata["flow"] == "noop"
    with pytest.raises(PlanNotFoundError):
        registry.consume(stored.plan_id)


def test_server_store_and_submit_stored_plan() -> None:
    from palm.runtimes.server import ServerRuntime

    rt = ServerRuntime()
    rt.start(port=0, http=False)
    try:
        bundle = rt.executor.prepare_process_plan(
            ProcessDefinition(
                name="pipeline",
                flows=[
                    FlowDefinition(name="extract", pattern="etl"),
                    FlowDefinition(name="graph", pattern="dag"),
                ],
            )
        )
        assert isinstance(bundle, ProcessPlan)
        stored = rt.store_process_plan(bundle)
        assert len(stored) == 2
        jobs = rt.submit_stored_plans([item.plan_id for item in stored])
        assert len(jobs) == 2
    finally:
        rt.stop()
