"""
Plan preparation helpers — shared between server surfaces and CQRS handlers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.plans import ExecutionPlan, ProcessPlan
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime


def prepare_flow_from_body(runtime: BaseRuntime, body: dict[str, object]) -> ExecutionPlan:
    """Build a flow plan from an HTTP-style request body."""
    if "flow" in body and isinstance(body["flow"], dict):
        flow = FlowDefinition.from_dict(body["flow"])
        return runtime.executor.prepare_flow_plan(flow, job_id=_optional_str(body.get("job_id")))

    if "wizard" in body:
        wizard = body["wizard"]
        if not isinstance(wizard, dict):
            raise TypeError("wizard must be an object")
        steps = wizard.get("steps")
        flow = FlowDefinition(
            name=str(wizard.get("name", "wizard")),
            pattern="wizard",
            options={"steps": int(steps)} if steps is not None else {},
        )
        return runtime.executor.prepare_flow_plan(flow, job_id=_optional_str(body.get("job_id")))

    if "flow_name" in body:
        return runtime.executor.prepare_flow_plan(
            str(body["flow_name"]),
            by_id=bool(body.get("by_id", False)),
            job_id=_optional_str(body.get("job_id")),
        )

    raise ValueError("expected 'flow', 'wizard', or 'flow_name' in request body")


def prepare_process_from_body(runtime: BaseRuntime, body: dict[str, object]) -> ProcessPlan:
    """Build a process plan bundle from an HTTP-style request body."""
    if "process" in body and isinstance(body["process"], dict):
        process = ProcessDefinition.from_dict(body["process"])
        return runtime.executor.prepare_process_plan(
            process,
            job_id=_optional_str(body.get("job_id")),
        )

    if "process_name" in body:
        return runtime.executor.prepare_process_plan(
            str(body["process_name"]),
            by_id=bool(body.get("by_id", False)),
            job_id=_optional_str(body.get("job_id")),
        )

    raise ValueError("expected 'process' or 'process_name' in request body")


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None
