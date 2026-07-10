"""
Todo analytics interaction flow — load stored todos and rebuild published views.

Resources alone are not the product; this flow is the operator path that
**uses** the definitions.

::

    palm flow start todo-analytics
"""

from __future__ import annotations

from typing import Any

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.patterns.wizard.bindings.compensation.handler import (
    CommitResult,
    default_commit_registry,
)

from .resources import priority_rollup

TODO_ANALYTICS_FLOW = FlowDefinition(
    id="flow-todo-analytics",
    name="todo-analytics",
    pattern="wizard",
    options={
        "include_summary": True,
        "include_commit": True,
        "commit_hook": "rebuild_todo_analytics",
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "intro",
                "title": "Palm todo analytics",
                "prompt": (
                    "Palm dogfood analytics — not a business BI demo. "
                    "Load todos persisted by todo-builder, then rebuild the "
                    "published priority view for /analytics and AnalyticsService."
                ),
                "step_kind": "introduction",
                "required": False,
            },
            {
                "slug": "load_todos",
                "title": "Load stored todos",
                "prompt": "Fetch palm-todos from kv",
                "step_kind": "resource",
                "resource_ref": "palm-todos",
                "output_key": "todo_store",
            },
        ],
    },
)

TODO_ANALYTICS_PROCESS = ProcessDefinition(
    id="proc-todo-analytics",
    name="todo-analytics-process",
    flows=[TODO_ANALYTICS_FLOW],
    metadata={
        "example": True,
        "description": "Interactive refresh of palm-todos analytics views",
    },
)


def _items_from_store(store: Any) -> list[dict[str, Any]]:
    if not isinstance(store, dict):
        return []
    value = store.get("value") if "value" in store else store
    if isinstance(value, dict):
        items = value.get("items")
        if isinstance(items, list):
            return [i for i in items if isinstance(i, dict)]
    items = store.get("items")
    if isinstance(items, list):
        return [i for i in items if isinstance(i, dict)]
    return []


def _rebuild_todo_analytics(ctx: object) -> CommitResult:
    answers = getattr(ctx, "answers", {}) or {}
    items = _items_from_store(answers.get("todo_store"))
    if not items:
        return CommitResult.failure(
            "No todos loaded — run todo-builder first or seed materialize_todo_analytics"
        )
    fact = {"items": items, "count": len(items)}
    view = {"items": priority_rollup(items)}
    engine = getattr(ctx, "resource_engine", None)
    if engine is None:
        return CommitResult.failure("ResourceEngine not available")
    if not getattr(engine, "is_initialized", True):
        engine.initialize()
    put_fact = engine.invoke("put-palm-todos", params={"value": fact})
    if not put_fact.success:
        return CommitResult.failure(put_fact.error or "put palm-todos failed")
    put_view = engine.invoke("put-palm-todos-by-priority", params={"value": view})
    if not put_view.success:
        return CommitResult.failure(put_view.error or "put priority view failed")
    return CommitResult.success(
        {
            "count": len(items),
            "priority_rollup": view["items"],
            "datasets": ["palm-todos", "palm-todos-by-priority"],
        }
    )


def register_definitions(repository: object) -> None:
    """Register flow/process + commit hook only (resources via package ``__init__``)."""
    default_commit_registry().register(
        "rebuild_todo_analytics", _rebuild_todo_analytics
    )
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(TODO_ANALYTICS_FLOW)
    if callable(save_process):
        save_process(TODO_ANALYTICS_PROCESS)


__all__ = [
    "TODO_ANALYTICS_FLOW",
    "TODO_ANALYTICS_PROCESS",
    "register_definitions",
]
