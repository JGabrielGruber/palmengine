"""
State snapshot helpers — serialize and restore execution state with schema metadata.
"""

from __future__ import annotations

from typing import Any

from palm.core.context import BaseState, DictStateSchema, StateSchema
from palm.states import BlackboardState

SNAPSHOT_META_KEY = "__palm:meta"


def snapshot_meta(state: BaseState) -> dict[str, Any]:
    """Return schema, scope stack, and per-scope schema metadata."""
    meta: dict[str, Any] = {}
    schema_doc = _schema_document(state.schema)
    if schema_doc is not None:
        meta["schema"] = schema_doc

    stack = state.scope_stack()
    if stack:
        meta["scope_stack"] = list(stack)
    scope = state.current_scope()
    if scope is not None:
        meta["current_scope"] = scope
    depth = state.scope_depth()
    if depth:
        meta["scope_depth"] = depth

    scope_schema_docs = _scope_schema_documents(state.scope_schemas())
    if scope_schema_docs:
        meta["scope_schemas"] = scope_schema_docs

    effective = state.effective_schema()
    effective_doc = _schema_document(effective)
    if effective_doc is not None:
        meta["effective_schema"] = effective_doc

    return meta


def snapshot_state(state: BaseState) -> dict[str, Any]:
    """Serialize execution state for storage, including schema metadata."""
    data = dict(state.snapshot())
    meta = snapshot_meta(state)
    if meta:
        data[SNAPSHOT_META_KEY] = meta
    return data


def state_from_snapshot(data: dict[str, Any]) -> BlackboardState:
    """Restore ``BlackboardState`` from a persisted snapshot."""
    raw = dict(data)
    meta = raw.pop(SNAPSHOT_META_KEY, None)
    schema, scope_schemas = _schemas_from_meta(meta)
    state = BlackboardState(raw, schema=schema)
    if scope_schemas:
        state.restore_scope_schemas(scope_schemas)
    _restore_scope_stack(state, meta)
    return state


def _restore_scope_stack(state: BaseState, meta: Any) -> None:
    if not isinstance(meta, dict):
        return
    stack = meta.get("scope_stack")
    if isinstance(stack, list) and stack:
        state.restore_scope_stack([str(name) for name in stack])
        return
    scope = meta.get("current_scope")
    if scope is not None:
        state.restore_scope_stack([str(scope)])


def _schema_document(schema: StateSchema | None) -> dict[str, Any] | None:
    if schema is None:
        return None
    definition = schema.definition
    if isinstance(definition, dict):
        return dict(definition)
    return None


def _scope_schema_documents(schemas: dict[str, StateSchema]) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for name, schema in schemas.items():
        document = _schema_document(schema)
        if document is not None:
            documents[name] = document
    return documents


def _schemas_from_meta(
    meta: Any,
) -> tuple[StateSchema | None, dict[str, StateSchema]]:
    if not isinstance(meta, dict):
        return None, {}

    root_schema: StateSchema | None = None
    document = meta.get("schema")
    if isinstance(document, dict):
        root_schema = DictStateSchema(document)

    scope_schemas: dict[str, StateSchema] = {}
    raw_scope_schemas = meta.get("scope_schemas")
    if isinstance(raw_scope_schemas, dict):
        for name, scoped_doc in raw_scope_schemas.items():
            if isinstance(scoped_doc, dict):
                scope_schemas[str(name)] = DictStateSchema(scoped_doc)

    return root_schema, scope_schemas