"""Tests for ProcessPlan batch preparation."""

from __future__ import annotations

from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition, ProcessDefinition
from palm.executions import ProcessPlan
from palm.runtimes.embedded import EmbeddedRuntime


def test_prepare_process_plan_without_submit() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        process = ProcessDefinition(
            name="pipeline",
            flows=[
                FlowDefinition(name="extract", pattern="etl"),
                FlowDefinition(name="graph", pattern="dag"),
            ],
        )
        bundle = rt.executor.prepare_process_plan(process)
        assert isinstance(bundle, ProcessPlan)
        assert len(bundle.plans) == 2
        assert bundle.plans[0].metadata["process"] == "pipeline"
        assert bundle.plans[1].metadata["process"] == "pipeline"
    finally:
        rt.stop()


def test_submit_plans_matches_submit_process() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        process = ProcessDefinition(
            name="pipeline",
            flows=[
                FlowDefinition(name="extract", pattern="etl"),
                FlowDefinition(name="graph", pattern="dag"),
            ],
        )
        bundle = rt.executor.prepare_process_plan(process)
        jobs = rt.executor.submit_plans(bundle.plans)
        assert len(jobs) == 2
        assert jobs[0].status == JobStatus.SUCCEEDED
        assert jobs[1].status == JobStatus.SUCCEEDED
    finally:
        rt.stop()


def test_process_plan_submit_all() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        process = ProcessDefinition(
            name="solo",
            flows=[FlowDefinition(name="only", pattern="etl")],
        )
        bundle = rt.executor.prepare_process_plan(process)
        jobs = bundle.submit_all(rt.orchestration)
        assert len(jobs) == 1
        assert jobs[0].metadata["process"] == "solo"
    finally:
        rt.stop()