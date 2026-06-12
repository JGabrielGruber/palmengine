"""
State snapshot helpers — serialize and restore execution state with schema metadata.
"""

from __future__ import annotations

from typing import Any

from palm.core.context import BaseState, DictStateSchema, StateSchema
from palm.states import BlackboardState

SNAPSHOT_META_KEY = "__palm:meta"


def snapshot_meta(state: BaseState) -> dict[str, Any]:
    """Return schema and scope metadata for a state instance."""
    meta: dict[str, Any] = {}
    schema_doc = _schema_document(state.schema)
    if schema_doc is not None:
        meta["schema"] = schema_doc
    scope = state.current_scope()
    if scope is not None:
        meta["current_scope"] = scope
    depth = state.scope_depth()
    if depth:
        meta["scope_depth"] = depth
    return meta


def snapshot_state(state: BaseState) -> dict[str, Any]:
    """Serialize execution state for storage, including optional schema metadata."""
    data = dict(state.snapshot())
    meta = snapshot_meta(state)
    if meta:
        data[SNAPSHOT_META_KEY] = meta
    return data


def state_from_snapshot(data: dict[str, Any]) -> BlackboardState:
    """Restore ``BlackboardState`` from a persisted snapshot."""
    raw = dict(data)
    meta = raw.pop(SNAPSHOT_META_KEY, None)
    schema = _schema_from_meta(meta)
    return BlackboardState(raw, schema=schema)


def _schema_document(schema: StateSchema | None) -> dict[str, Any] | None:
    if schema is None:
        return None
    definition = schema.definition
    if isinstance(definition, dict):
        return dict(definition)
    return None


def _schema_from_meta(meta: Any) -> StateSchema | None:
    if not isinstance(meta, dict):
        return None
    document = meta.get("schema")
    if isinstance(document, dict):
        return DictStateSchema(document)
    return None