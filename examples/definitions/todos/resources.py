"""
Todo + Palm analytics resources (0.35 dogfood).

Durable list from **todo-builder** commit; published read resources for AnalyticsService.
Write resources stay unpublished (operator/flow materialize only).
"""

from __future__ import annotations

from typing import Any

from palm.definitions import ResourceDefinition

_NS = "palm"
_BACKEND = "auto"  # durable when host storage is durable; memory in tests

PUT_PALM_TODOS = ResourceDefinition(
    id="resource-put-palm-todos",
    name="put-palm-todos",
    provider="kv",
    action="put",
    resource_id="todos/list",
    params={"namespace": _NS, "backend": _BACKEND},
    metadata={
        "description": "Persist todo-builder list (write; not BI-published)",
        "tags": ["palm", "todo", "kv", "write"],
    },
)

PALM_TODOS = ResourceDefinition(
    id="resource-palm-todos",
    name="palm-todos",
    provider="kv",
    action="get",
    resource_id="todos/list",
    params={
        "namespace": _NS,
        "backend": _BACKEND,
        "default": {"items": [], "count": 0},
    },
    metadata={
        "description": "Stored todos from todo-builder (Palm analytics fact)",
        "tags": ["palm", "todo", "bi", "fact"],
        "analytics": {
            "published": True,
            "kind": "fact",
            "default_profile": "table",
            "row_path": "value.items",
            "refresh": {
                "flow_id": "todo-builder",
                "note": "Commit todo-builder or run todo-analytics refresh",
            },
        },
    },
)

PUT_PALM_TODOS_BY_PRIORITY = ResourceDefinition(
    id="resource-put-palm-todos-by-priority",
    name="put-palm-todos-by-priority",
    provider="kv",
    action="put",
    resource_id="todos/by-priority",
    params={"namespace": _NS, "backend": _BACKEND},
    metadata={
        "description": "Write priority rollup view",
        "tags": ["palm", "todo", "kv", "write"],
    },
)

PALM_TODOS_BY_PRIORITY = ResourceDefinition(
    id="resource-palm-todos-by-priority",
    name="palm-todos-by-priority",
    provider="kv",
    action="get",
    resource_id="todos/by-priority",
    params={
        "namespace": _NS,
        "backend": _BACKEND,
        "default": {"items": []},
    },
    metadata={
        "description": "Todos counted by priority (materialized view)",
        "tags": ["palm", "todo", "bi", "view"],
        "analytics": {
            "published": True,
            "kind": "view",
            "derived_from": ["palm-todos"],
            "default_profile": "series",
            "row_path": "value.items",
            "refresh": {"flow_id": "todo-analytics"},
        },
    },
)

SEED_TODO_ROWS: list[dict[str, Any]] = [
    {"title": "Ship analytics dogfood", "due_date": "2026-07-10", "priority": "high"},
    {"title": "Wire todo-builder kv", "due_date": "", "priority": "high"},
    {"title": "Polish /analytics UI", "due_date": "2026-07-12", "priority": "medium"},
    {"title": "Docs pass", "due_date": "", "priority": "low"},
]


def priority_rollup(todos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in todos:
        if not isinstance(item, dict):
            continue
        p = str(item.get("priority") or "unknown")
        counts[p] = counts.get(p, 0) + 1
    order = ("high", "medium", "low", "unknown")
    keys = [k for k in order if k in counts] + sorted(
        k for k in counts if k not in order
    )
    return [{"priority": k, "count": counts[k]} for k in keys]


def register_definitions(repository: object) -> None:
    save = getattr(repository, "save_resource", None)
    if not callable(save):
        return
    for res in (
        PUT_PALM_TODOS,
        PALM_TODOS,
        PUT_PALM_TODOS_BY_PRIORITY,
        PALM_TODOS_BY_PRIORITY,
    ):
        save(res)


def materialize_todo_analytics(
    providers: Any,
    *,
    todos: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Put fact + priority view (tests / seed without running wizards)."""
    items = list(todos if todos is not None else SEED_TODO_ROWS)
    fact = {"items": items, "count": len(items)}
    view = {"items": priority_rollup(items)}
    fact_put = providers.invoke("put-palm-todos", params={"value": fact})
    view_put = providers.invoke("put-palm-todos-by-priority", params={"value": view})
    return {
        "todo_rows": len(items),
        "priority_rows": len(view["items"]),
        "fact_put": fact_put,
        "view_put": view_put,
    }


__all__ = [
    "PALM_TODOS",
    "PALM_TODOS_BY_PRIORITY",
    "PUT_PALM_TODOS",
    "PUT_PALM_TODOS_BY_PRIORITY",
    "SEED_TODO_ROWS",
    "materialize_todo_analytics",
    "priority_rollup",
    "register_definitions",
]
