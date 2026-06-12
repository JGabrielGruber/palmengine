"""
Branch scope coordination — schema binding and isolated branch state snapshots.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.state.schema_binding import materialize_state_schema
from palm.core.context import BaseState
from palm.patterns.parallel.config import BranchConfig
from palm.patterns.parallel.keys import ParallelKeys

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.core.context import ContextEngine, StateSchema


def enter_branch(
    state: BaseState,
    branch: BranchConfig,
    *,
    repository: DefinitionRepository | None = None,
    context: ContextEngine | None = None,
) -> None:
    """Enter a branch scope and bind its optional schema."""
    schema = materialize_branch_schema(branch, repository)
    if schema is not None:
        state.bind_scope_schema(branch.slug, schema)

    if context is not None:
        if context.current_state is not state:
            context.bind_state(state)
        if context.current_state_scope != branch.slug:
            context.enter_state_scope(branch.slug)
        return

    if state.current_scope() != branch.slug:
        state.enter_scope(branch.slug)


def leave_branch(
    state: BaseState,
    branch: BranchConfig,
    *,
    context: ContextEngine | None = None,
) -> None:
    """Exit the branch scope when it matches ``branch.slug``."""
    if context is not None:
        if context.current_state_scope == branch.slug:
            context.exit_state_scope()
        return
    if state.current_scope() == branch.slug:
        state.exit_scope()


def materialize_branch_schema(
    branch: BranchConfig,
    repository: DefinitionRepository | None = None,
) -> StateSchema | None:
    return materialize_state_schema(
        inline=branch.state_schema,
        ref=branch.state_schema_ref,
        repository=repository,
    )


def save_branch_snapshot(state: BaseState, snapshot: dict[str, Any]) -> None:
    """Persist an isolated branch blackboard under the active branch scope."""
    state.set_scoped(ParallelKeys.BRANCH_STATE, snapshot)


def load_branch_snapshot(state: BaseState) -> dict[str, Any] | None:
    raw = state.get_scoped(ParallelKeys.BRANCH_STATE)
    return dict(raw) if isinstance(raw, dict) else None


def load_branch_snapshot_for(state: BaseState, branch_slug: str) -> dict[str, Any] | None:
    """Load a branch blackboard snapshot without entering the branch scope."""
    storage = state.scope_storage()
    if storage is None:
        return None
    from palm.core.context.scoping import SCOPES_ROOT_KEY

    scopes_root = storage.get(SCOPES_ROOT_KEY)
    if not isinstance(scopes_root, dict):
        return None
    node = scopes_root.get(branch_slug)
    if not isinstance(node, dict):
        return None
    raw = node.get(ParallelKeys.BRANCH_STATE)
    return dict(raw) if isinstance(raw, dict) else None