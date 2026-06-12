"""
Branch runner — isolated sub-workflow execution inside a parent scope.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.persistence.state_snapshot import snapshot_state, state_from_snapshot
from palm.common.state.schema_binding import bind_schema_to_state
from palm.core.behavior_tree import BasePattern, PatternStatus
from palm.core.context import BaseState
from palm.core.orchestration.input_capable import InputCapable, StepInspectable
from palm.patterns.parallel.config import BranchConfig
from palm.patterns.parallel.keys import ParallelKeys
from palm.patterns.parallel.merge import record_branch_result
from palm.patterns.parallel.scope import (
    enter_branch,
    leave_branch,
    load_branch_snapshot,
    materialize_branch_schema,
    save_branch_snapshot,
)
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.core.context import ContextEngine


class BranchRunner:
    """Execute one sub-workflow in an isolated branch blackboard."""

    def __init__(
        self,
        branch: BranchConfig,
        executable: BasePattern,
        *,
        context_engine: ContextEngine | None = None,
        repository: DefinitionRepository | None = None,
    ) -> None:
        self.branch = branch
        self.executable = executable
        self._context = context_engine
        self._repository = repository
        self._branch_state: BlackboardState | None = None
        self._scope_entered = False
        self._completed = False

    @property
    def completed(self) -> bool:
        return self._completed

    def tick(self, parent: BaseState) -> PatternStatus:
        if self._completed:
            return PatternStatus.SUCCESS

        self._ensure_scope(parent)
        branch_state = self._ensure_branch_state(parent)
        status = self.executable.tick(branch_state)
        save_branch_snapshot(parent, self.branch.slug, snapshot_state(branch_state))

        if status == PatternStatus.WAITING_FOR_INPUT:
            if parent.get(ParallelKeys.ACTIVE_BRANCH) is None:
                parent.set(ParallelKeys.ACTIVE_BRANCH, self.branch.slug)
            return status

        if status == PatternStatus.RUNNING:
            return status

        if status == PatternStatus.SUCCESS:
            self._finalize_success(parent, branch_state)
            return PatternStatus.SUCCESS

        self._teardown_scope(parent)
        return PatternStatus.FAILURE

    def provide_input(self, parent: BaseState, value: Any) -> str | None:
        if not isinstance(self.executable, InputCapable):
            return None
        self._ensure_scope(parent)
        branch_state = self._ensure_branch_state(parent)
        slug = self.executable.provide_input(branch_state, value)
        save_branch_snapshot(parent, self.branch.slug, snapshot_state(branch_state))
        parent.set(ParallelKeys.ACTIVE_BRANCH, self.branch.slug)
        if slug:
            return f"{self.branch.slug}:{slug}"
        return self.branch.slug

    def current_step_slug(self, parent: BaseState) -> str | None:
        if self._branch_state is None:
            snapshot = load_branch_snapshot(parent, self.branch.slug)
            if snapshot is None:
                return None
            self._branch_state = state_from_snapshot(snapshot)
        if isinstance(self.executable, StepInspectable):
            inner = self.executable.current_step_slug(self._branch_state)
            if inner:
                return f"{self.branch.slug}:{inner}"
        return self.branch.slug

    def branch_answers(self, parent: BaseState) -> dict[str, Any]:
        if self._branch_state is None:
            snapshot = load_branch_snapshot(parent, self.branch.slug)
            if snapshot is None:
                return {}
            self._branch_state = state_from_snapshot(snapshot)
        if isinstance(self.executable, StepInspectable):
            return dict(self.executable.answers(self._branch_state))
        return {}

    def mark_completed(self) -> None:
        self._completed = True

    def restore_completed(self, *, completed: bool) -> None:
        self._completed = completed

    def restore_scope_entered(self, *, entered: bool) -> None:
        self._scope_entered = entered

    def _ensure_scope(self, parent: BaseState) -> None:
        if self._scope_entered:
            return
        enter_branch(
            parent,
            self.branch,
            repository=self._repository,
            context=self._context,
        )
        self._scope_entered = True

    def _ensure_branch_state(self, parent: BaseState) -> BlackboardState:
        if self._branch_state is not None:
            return self._branch_state

        snapshot = load_branch_snapshot(parent, self.branch.slug)
        if snapshot:
            self._branch_state = state_from_snapshot(snapshot)
            return self._branch_state

        schema = materialize_branch_schema(self.branch, self._repository)
        self._branch_state = BlackboardState(schema=schema)
        bind_schema_to_state(self._branch_state, schema)
        save_branch_snapshot(parent, self.branch.slug, snapshot_state(self._branch_state))
        return self._branch_state

    def _finalize_success(self, parent: BaseState, branch_state: BlackboardState) -> None:
        record_branch_result(parent, self.branch, self._build_result(branch_state))
        self._completed = True
        self._branch_state = None
        parent.delete(ParallelKeys.ACTIVE_BRANCH)
        self._teardown_scope(parent)

    def _teardown_scope(self, parent: BaseState) -> None:
        if not self._scope_entered:
            return
        leave_branch(parent, self.branch, context=self._context)
        self._scope_entered = False

    def _build_result(self, branch_state: BlackboardState) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": "success",
            "slug": self.branch.slug,
            "pattern": getattr(self.executable, "name", self.branch.pattern or ""),
        }
        if isinstance(self.executable, StepInspectable):
            payload["answers"] = self.executable.answers(branch_state)
        else:
            payload["value"] = branch_state.snapshot()
        return payload