"""
ParallelPattern — run multiple sub-workflows with scoped isolation and merge.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import BasePattern, ParallelNode, PatternStatus, RootNode
from palm.core.context import BaseState, ContextEngine
from palm.core.event import EventEngine
from palm.core.exceptions import StateValidationError
from palm.core.orchestration.input_capable import InputCapable, StepInspectable
from palm.patterns.parallel.bindings.behavior_tree.tree import build_parallel_tree
from palm.patterns.parallel.bindings.context.keys import ParallelKeys
from palm.patterns.parallel.bindings.definitions.config import ParallelConfig
from palm.patterns.parallel.flow.branch import BranchRunner
from palm.patterns.parallel.flow.merge import get_branch_results, merge_branch_results


class ParallelPattern(BasePattern, InputCapable, StepInspectable):
    """
    Execute branches in parallel (interleaved ticks) with per-branch scopes.

    Each branch runs a sub-workflow in an isolated blackboard snapshotted under
    its scope. When branches complete, results merge per ``merge_strategy``.
    """

    def __init__(
        self,
        *,
        name: str = "parallel",
        config: ParallelConfig | None = None,
        runners: list[BranchRunner] | None = None,
        event_engine: EventEngine | None = None,
        context_engine: ContextEngine | None = None,
    ) -> None:
        super().__init__(name=name)
        if config is None:
            raise ValueError("ParallelPattern requires ParallelConfig")
        if not runners:
            raise ValueError("ParallelPattern requires at least one BranchRunner")
        self._config = config
        self._runners = {runner.branch.slug: runner for runner in runners}
        self._event_engine = event_engine
        self._context_engine = context_engine
        self._root: RootNode
        self._parallel: ParallelNode
        self._root, self._parallel = build_parallel_tree(name, config, runners)

    @property
    def config(self) -> ParallelConfig:
        return self._config

    @property
    def root(self) -> RootNode:
        return self._root

    @property
    def parallel(self) -> ParallelNode:
        return self._parallel

    def tick(self, state: BaseState) -> PatternStatus:
        if self._context_engine is not None and self._context_engine.current_state is not state:
            self._context_engine.bind_state(state)

        if state.get(ParallelKeys.COMPLETED) or state.get(ParallelKeys.MERGE_COMPLETE):
            return PatternStatus.SUCCESS

        status = self._root.tick(state)
        if status == PatternStatus.WAITING_FOR_INPUT:
            self._emit_branch_waiting(state)
            return status
        if status != PatternStatus.SUCCESS:
            return status

        try:
            merge_branch_results(state, self._config)
        except StateValidationError:
            return PatternStatus.FAILURE

        state.set(ParallelKeys.COMPLETED, True)
        self._emit_completed(state)
        return PatternStatus.SUCCESS

    def reset(self) -> None:
        self._root.reset()

    def provide_input(self, state: BaseState, value: Any) -> str | None:
        active = state.get(ParallelKeys.ACTIVE_BRANCH)
        if not isinstance(active, str):
            return None
        runner = self._runners.get(active)
        if runner is None:
            return None
        slug = runner.provide_input(state, value)
        state.delete(ParallelKeys.ACTIVE_BRANCH)
        return slug

    def current_step_slug(self, state: BaseState) -> str | None:
        active = state.get(ParallelKeys.ACTIVE_BRANCH)
        if isinstance(active, str):
            runner = self._runners.get(active)
            if runner is not None:
                return runner.current_step_slug(state)
        for slug, runner in self._runners.items():
            if not runner.completed:
                return runner.current_step_slug(state) or slug
        return None

    def answers(self, state: BaseState) -> dict[str, Any]:
        merged = state.get(ParallelKeys.MERGED)
        if isinstance(merged, dict):
            return dict(merged)
        return get_branch_results(state)

    def branch_runners(self) -> dict[str, BranchRunner]:
        return dict(self._runners)

    def _emit_branch_waiting(self, state: BaseState) -> None:
        if self._event_engine is None:
            return
        active = state.get(ParallelKeys.ACTIVE_BRANCH)
        if not isinstance(active, str):
            return
        runner = self._runners.get(active)
        step = runner.current_step_slug(state) if runner is not None else None
        self._event_engine.emit(
            "parallel.branch_waiting",
            pattern=self.name,
            branch=active,
            step=step,
        )

    def _emit_completed(self, state: BaseState) -> None:
        if self._event_engine is None:
            return
        self._event_engine.emit(
            "parallel.completed",
            pattern=self.name,
            merged=state.get(ParallelKeys.MERGED, {}),
        )
