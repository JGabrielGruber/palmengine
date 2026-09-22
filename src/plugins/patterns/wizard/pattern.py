"""
WizardPattern — thin orchestrator over a behavior-tree of wizard phases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.core.behavior_tree import BasePattern, PatternStatus, RootNode
from palm.core.context import BaseState, ContextEngine
from palm.core.event import EventContext, EventEngine
from palm.core.orchestration.input_capable import JobInspectable
from palm.core.resource.invoker import ResourceInvoker
from palm.core.workload.driver import WorkloadDriver
from plugins.patterns.wizard.bindings.behavior_tree.backtrack import (
    WizardSequenceNode,
    request_backtrack,
)
from plugins.patterns.wizard.bindings.inspection import inspect_wizard_job

if TYPE_CHECKING:
    from palm.common.job_inspection import JobContext
    from palm.core.orchestration import Job
from plugins.patterns.wizard.bindings.behavior_tree.tree import build_wizard_tree
from plugins.patterns.wizard.bindings.compensation.handler import (
    CommitRegistry,
    default_commit_registry,
)
from plugins.patterns.wizard.bindings.context.keys import WizardKeys
from plugins.patterns.wizard.bindings.definitions.config import WizardConfig
from plugins.patterns.wizard.flow.phases._base import provide_wizard_input


class WizardPattern(BasePattern, JobInspectable):
    """
    Interactive wizard driven entirely by its behavior tree.

    Phase logic (input, collection, summary, commit, resource, workload,
    transform, backtrack, completion) lives under ``palm.patterns.wizard.flow.phases``.
    """

    def __init__(
        self,
        *,
        name: str = "wizard",
        config: WizardConfig | None = None,
        steps: int | None = None,
        event_engine: EventEngine | None = None,
        resource_engine: ResourceInvoker | None = None,
        workload_engine: WorkloadDriver | None = None,
        commit_registry: CommitRegistry | None = None,
        context_engine: ContextEngine | None = None,
    ) -> None:
        super().__init__(name=name)
        if config is None:
            count = steps if steps is not None else 1
            config = WizardConfig.from_slugs([f"step_{i + 1}" for i in range(count)])
        self._config = config
        self._event_engine = event_engine
        self._resource_engine = resource_engine
        self._workload_engine = workload_engine
        self._commit_registry = commit_registry or default_commit_registry()
        self._context_engine = context_engine
        self._root: RootNode
        self._sequence: WizardSequenceNode
        self._root, self._sequence = build_wizard_tree(
            name,
            self._config,
            emit=self._bridge_emit,
            commit_registry=self._commit_registry,
            resource_engine=self._resource_engine,
            workload_engine=self._workload_engine,
            context_engine=self._context_engine,
        )

    @property
    def config(self) -> WizardConfig:
        return self._config

    @property
    def root(self) -> RootNode:
        return self._root

    @property
    def sequence(self) -> WizardSequenceNode:
        return self._sequence

    @property
    def commit_registry(self) -> CommitRegistry:
        return self._commit_registry

    def tick(self, state: BaseState) -> PatternStatus:
        if self._context_engine is not None and self._context_engine.current_state is not state:
            self._context_engine.bind_state(state)
        return self._root.tick(state)

    def reset(self) -> None:
        self._root.reset()

    def provide_input(self, state: BaseState, value: Any) -> str | None:
        return provide_wizard_input(state, value)

    def request_backtrack(self, state: BaseState, to_slug: str) -> None:
        request_backtrack(
            state,
            self._config,
            to_slug,
            emit=self._bridge_emit,
            wizard_name=self.name,
        )

    def current_step_slug(self, state: BaseState) -> str | None:
        value = state.get(WizardKeys.CURRENT_STEP)
        return str(value) if value is not None else None

    def answers(self, state: BaseState) -> dict[str, Any]:
        raw = state.get(WizardKeys.ANSWERS)
        return dict(raw) if isinstance(raw, dict) else {}

    def inspect_job(self, job: Job) -> JobContext:
        return inspect_wizard_job(self, job)

    def is_committed(self, state: BaseState) -> bool:
        return bool(state.get(WizardKeys.COMMITTED))

    def _bridge_emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._event_engine is not None:
            context = self._event_context()
            self._event_engine.emit(event_type, context=context, **payload)

    def _event_context(self) -> EventContext | None:
        if self._context_engine is None:
            return None
        return EventContext.from_mapping(self._context_engine.current)


def default_wizard_config(step_count: int = 1) -> WizardConfig:
    return WizardConfig.from_slugs([f"step_{i + 1}" for i in range(step_count)])
