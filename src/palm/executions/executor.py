"""
Definition executor — submits flows and processes via a runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

from palm.core.orchestration import Job
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.executions.build_context import PatternBuildContext
from palm.executions.builder import build_pattern
from palm.executions.exceptions import DefinitionBuildError, DefinitionNotFoundError
from palm.executions.repository import DefinitionRepository
from palm.executions.wizard_options import wizard_metadata_from_flow
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.core.context import BaseState
    from palm.runtimes.embedded import EmbeddedRuntime


class DefinitionExecutor:
    """
    Bridges declarative definitions to orchestration jobs.

    Accepts in-memory definitions, or resolves names/ids through a
    ``DefinitionRepository`` when a string reference is supplied.
    """

    def __init__(
        self,
        runtime: EmbeddedRuntime,
        repository: DefinitionRepository | None = None,
    ) -> None:
        self._runtime = runtime
        self._repository = repository

    @property
    def repository(self) -> DefinitionRepository | None:
        return self._repository

    @overload
    def submit_flow(
        self,
        flow: FlowDefinition,
        *,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job: ...

    @overload
    def submit_flow(
        self,
        flow: str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job: ...

    def submit_flow(
        self,
        flow: FlowDefinition | str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """Build a pattern from a flow (or repository ref) and submit a job."""
        resolved = self._resolve_flow(flow, by_id=by_id)
        self._require_runtime()
        build_ctx = PatternBuildContext(
            event_engine=self._runtime.event,
            resource_engine=getattr(self._runtime, "resource", None),
        )
        if resolved.pattern == "wizard":
            build_ctx.wizard_metadata = wizard_metadata_from_flow(resolved.options)

        pattern = build_pattern(resolved, context=build_ctx)
        job_state = state if state is not None else BlackboardState()
        meta = dict(metadata or {})
        meta.setdefault("definition_type", "flow")
        meta.setdefault("flow", resolved.name)
        meta.setdefault("flow_id", resolved.definition_id)
        meta.setdefault("pattern", resolved.pattern)
        if build_ctx.wizard_metadata:
            meta.setdefault("wizard", dict(build_ctx.wizard_metadata))
        return self._runtime.orchestration.submit(
            pattern,
            state=job_state,
            job_id=job_id,
            metadata=meta,
        )

    @overload
    def submit_process(
        self,
        process: ProcessDefinition,
        *,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]: ...

    @overload
    def submit_process(
        self,
        process: str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]: ...

    def submit_process(
        self,
        process: ProcessDefinition | str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]:
        """Submit one job per flow on a process (or repository ref)."""
        resolved = self._resolve_process(process, by_id=by_id)
        if not resolved.flows:
            raise DefinitionBuildError(f"Process {resolved.name!r} defines no flows")

        jobs: list[Job] = []
        for index, flow in enumerate(resolved.flows):
            flow_meta = dict(metadata or {})
            flow_meta.setdefault("definition_type", "process")
            flow_meta.setdefault("process", resolved.name)
            flow_meta.setdefault("process_id", resolved.definition_id)
            flow_meta.setdefault("storage", resolved.storage)
            if resolved.metadata:
                flow_meta.setdefault("process_metadata", dict(resolved.metadata))

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

    def submit_flow_by_name(
        self,
        name: str,
        *,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        return self.submit_flow(name, by_id=False, job_id=job_id, state=state, metadata=metadata)

    def submit_flow_by_id(
        self,
        definition_id: str,
        *,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        return self.submit_flow(
            definition_id,
            by_id=True,
            job_id=job_id,
            state=state,
            metadata=metadata,
        )

    def submit_process_by_name(
        self,
        name: str,
        *,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]:
        return self.submit_process(
            name,
            by_id=False,
            job_id=job_id,
            state=state,
            metadata=metadata,
        )

    def submit_process_by_id(
        self,
        definition_id: str,
        *,
        job_id: str | None = None,
        state: BaseState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Job]:
        return self.submit_process(
            definition_id,
            by_id=True,
            job_id=job_id,
            state=state,
            metadata=metadata,
        )

    def _resolve_flow(self, flow: FlowDefinition | str, *, by_id: bool) -> FlowDefinition:
        if isinstance(flow, FlowDefinition):
            return flow
        repo = self._repository
        if repo is None:
            raise DefinitionBuildError(
                "Cannot resolve flow by reference without a DefinitionRepository"
            )
        try:
            return repo.get_flow(flow, by_id=by_id)
        except DefinitionNotFoundError as exc:
            raise DefinitionBuildError(str(exc)) from exc

    def _resolve_process(
        self, process: ProcessDefinition | str, *, by_id: bool
    ) -> ProcessDefinition:
        if isinstance(process, ProcessDefinition):
            return process
        repo = self._repository
        if repo is None:
            raise DefinitionBuildError(
                "Cannot resolve process by reference without a DefinitionRepository"
            )
        try:
            return repo.get_process(process, by_id=by_id)
        except DefinitionNotFoundError as exc:
            raise DefinitionBuildError(str(exc)) from exc

    def _require_runtime(self) -> None:
        if not self._runtime.is_started:
            raise RuntimeError(
                "EmbeddedRuntime is not started; call start() before submitting definitions"
            )


ProcessExecutor = DefinitionExecutor