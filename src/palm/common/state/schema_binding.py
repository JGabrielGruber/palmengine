"""
State schema binding — resolve declarative schemas and attach them to runtime state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState, DictStateSchema, StateSchema

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.definitions.flow import FlowDefinition


def materialize_state_schema(
    *,
    inline: dict[str, Any] | None = None,
    ref: str | None = None,
    repository: DefinitionRepository | None = None,
) -> StateSchema | None:
    """Build a core schema from an inline document or repository reference."""
    if inline:
        return DictStateSchema(inline)
    if not ref or repository is None:
        return None
    from palm.common.exceptions import DefinitionNotFoundError

    try:
        definition = repository.get_schema(ref)
    except DefinitionNotFoundError:
        try:
            definition = repository.get_schema(ref, by_id=True)
        except DefinitionNotFoundError:
            return None
    return definition.to_state_schema()


def bind_schema_to_state(state: BaseState, schema: StateSchema | None) -> None:
    """Attach ``schema`` and apply defaults when the state has no schema yet."""
    if schema is None or state.schema is not None:
        return
    state.bind_schema(schema)
    state.apply_defaults()


def bind_flow_state_schema(
    flow: FlowDefinition,
    state: BaseState,
    *,
    repository: DefinitionRepository | None = None,
) -> None:
    """Resolve and bind the schema declared on ``flow``."""
    schema = flow.materialize_state_schema(repository)
    bind_schema_to_state(state, schema)