"""
Flow submission preparation — definitions to orchestration-ready payloads.

Pattern-specific metadata enrichment registers via
:mod:`palm.patterns._registry` (e.g. wizard in ``palm.patterns.wizard.submission``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.common.patterns.build_context import PatternBuildContext
from palm.common.patterns.builder import build_pattern
from palm.common.persistence.instance_sync import prepare_resume_state
from palm.common.plans.execution_plan import ExecutionPlan
from palm.core.context import BaseState
from palm.definitions.flow import FlowDefinition
from palm.instances import ProcessInstance
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.common.persistence.instance_repository import InstanceRepository


@dataclass(frozen=True)
class FlowSubmission:
    """Orchestration-ready product of a flow definition build."""

    flow: FlowDefinition
    executable: Any
    state: BaseState
    metadata: dict[str, Any]
    instance_id: str | None

    def to_plan(self, *, job_id: str | None = None) -> ExecutionPlan:
        """Convert this submission into an :class:`~palm.common.plans.execution_plan.ExecutionPlan`."""
        return ExecutionPlan(
            executable=self.executable,
            state=self.state,
            metadata=self.metadata,
            job_id=job_id,
        )


def prepare_flow_submission(
    flow: FlowDefinition,
    *,
    state: BaseState | None,
    metadata: dict[str, Any] | None,
    instances: InstanceRepository | None,
    build_ctx: PatternBuildContext,
    instance_id: str | None = None,
) -> FlowSubmission:
    """Build a pattern executable and job metadata from a flow definition."""
    executable = build_pattern(flow, context=build_ctx)
    job_state = state if state is not None else BlackboardState()
    meta = dict(metadata or {})
    meta.setdefault("definition_type", "flow")
    meta.setdefault("flow", flow.name)
    meta.setdefault("flow_id", flow.definition_id)
    meta.setdefault("pattern", flow.pattern)
    meta["flow_definition"] = flow.to_dict()
    _apply_pattern_submission_metadata(flow, meta)

    iid = instance_id
    if iid is None and instances is not None:
        iid = instances.new_instance_id()
    if iid is not None:
        meta["instance_id"] = iid

    return FlowSubmission(
        flow=flow,
        executable=executable,
        state=job_state,
        metadata=meta,
        instance_id=iid,
    )


def prepare_resume_submission(
    instance: ProcessInstance,
    *,
    build_ctx: PatternBuildContext,
) -> FlowSubmission:
    """Rebuild a submission payload from a persisted process instance."""
    flow = FlowDefinition.from_dict(instance.flow_definition)
    executable = build_pattern(flow, context=build_ctx)
    state = prepare_resume_state(instance, executable)
    meta = dict(instance.metadata)
    meta["instance_id"] = instance.instance_id
    meta["resumed"] = True
    meta["flow_definition"] = instance.flow_definition

    return FlowSubmission(
        flow=flow,
        executable=executable,
        state=state,
        metadata=meta,
        instance_id=instance.instance_id,
    )


def _apply_pattern_submission_metadata(flow: FlowDefinition, meta: dict[str, Any]) -> None:
    import palm.patterns  # noqa: F401 — register pattern extension hooks

    from palm.patterns._registry import get_submission_metadata

    enricher = get_submission_metadata(flow.pattern)
    if enricher is None:
        return
    extra = enricher(flow)
    for key, value in extra.items():
        meta.setdefault(key, value)