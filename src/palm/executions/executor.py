"""
Definition executor — submits flows and processes via a runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.core.orchestration import Job
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.executions.builder import build_pattern
from palm.executions.exceptions import DefinitionBuildError
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.core.context import BaseState
    from palm.runtimes.embedded import EmbeddedRuntime


class DefinitionExecutor:
    """
    Bridges declarative definitions to orchestration jobs.

    Uses ``pattern_registry`` for resolution and delegates submission to the
    wired ``EmbeddedRuntime`` (context, events, orchestration unchanged).
    """

    def __init__(self, runtime: EmbeddedRuntime) -> None:
        self._runtime = runtime

    def submit_flow(
        self,
        flow: FlowDefinition,
        *,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """Build a pattern from ``flow`` and submit it as an orchestration job."""
        self._require_runtime()
        pattern = build_pattern(flow, event_engine=self._runtime.event)
        job_state = state if state is not None else BlackboardState()
        meta = dict(metadata or {})
        meta.setdefault("definition_type", "flow")
        meta.setdefault("flow", flow.name)
        meta.setdefault("pattern", flow.pattern)
        return self._runtime.orchestration.submit(
            pattern,
            state=job_state,
            job_id=job_id,
            metadata=meta,
        )

    def submit_process(
        self,
        process: ProcessDefinition,
        *,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]:
        """Submit one job per flow defined on ``process``."""
        if not process.flows:
            raise DefinitionBuildError(f"Process {process.name!r} defines no flows")

        jobs: list[Job] = []
        for index, flow in enumerate(process.flows):
            flow_meta = dict(metadata or {})
            flow_meta.setdefault("definition_type", "process")
            flow_meta.setdefault("process", process.name)
            flow_meta.setdefault("storage", process.storage)
            if process.metadata:
                flow_meta.setdefault("process_metadata", dict(process.metadata))

            assigned_id = job_id if index == 0 else None
            jobs.append(
                self.submit_flow(
                    flow,
                    job_id=assigned_id,
                    state=state,
                    metadata=flow_meta,
                )
            )
        return jobs

    def _require_runtime(self) -> None:
        if not self._runtime.is_started:
            raise RuntimeError(
                "EmbeddedRuntime is not started; call start() before submitting definitions"
            )


ProcessExecutor = DefinitionExecutor