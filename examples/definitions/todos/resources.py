"""
Todo resources — kv contracts only (definition pack).

Flows bind state into these via ``{{ state.* }}`` (see builder / analytics).
Published get resources are Analytics datasets; put resources are unpublished.
"""

from __future__ import annotations

from typing import Any

from palm.definitions import ResourceDefinition

_NS = "palm"
_BACKEND = "auto"

# Writes — not analytics-published
PUT_PALM_TODOS = ResourceDefinition(
    id="resource-put-palm-todos",
    name="put-palm-todos",
    provider="kv",
    action="put",
    resource_id="todos/list",
    params={
        "namespace": _NS,
        "backend": _BACKEND,
        "value": "{{ state.todos }}",
    },
    metadata={
        "description": "Persist todo list (wizard state.todos)",
        "tags": ["palm", "todo", "kv", "write"],
    },
)

PUT_PALM_TODOS_BY_PRIORITY = ResourceDefinition(
    id="resource-put-palm-todos-by-priority",
    name="put-palm-todos-by-priority",
    provider="kv",
    action="put",
    resource_id="todos/by-priority",
    params={
        "namespace": _NS,
        "backend": _BACKEND,
        "value": "{{ state.todos_by_priority }}",
    },
    metadata={
        "description": "Persist priority rollup (state.todos_by_priority from count_by)",
        "tags": ["palm", "todo", "kv", "write"],
    },
)

# Reads — BI published (AnalyticsService)
PALM_TODOS = ResourceDefinition(
    id="resource-palm-todos",
    name="palm-todos",
    provider="kv",
    action="get",
    resource_id="todos/list",
    params={
        "namespace": _NS,
        "backend": _BACKEND,
        "default": [],
    },
    metadata={
        "description": "Todos from todo-builder (fact rows)",
        "tags": ["palm", "todo", "bi", "fact"],
        "analytics": {
            "published": True,
            "kind": "fact",
            "default_profile": "table",
            "row_path": "value",
            "refresh": {"flow_id": "todo-builder"},
        },
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
        "default": [],
    },
    metadata={
        "description": "Todos by priority — virtual view (count_by on palm-todos)",
        "tags": ["palm", "todo", "bi", "view"],
        "analytics": {
            "published": True,
            "kind": "view",
            "source": "palm-todos",
            "materialize": False,
            "transform": {"op": "count_by", "field": "priority"},
            "derived_from": ["palm-todos"],
            "default_profile": "series",
            "fields": [
                {"name": "priority", "role": "dimension"},
                {"name": "count", "role": "measure", "type": "integer"},
            ],
        },
    },
)

SEED_TODO_ROWS: list[dict[str, Any]] = [
    {"title": "Ship analytics dogfood", "due_date": "2026-07-10", "priority": "high"},
    {"title": "Wire todo-builder kv", "due_date": "", "priority": "high"},
    {"title": "Polish /analytics UI", "due_date": "2026-07-12", "priority": "medium"},
    {"title": "Docs pass", "due_date": "", "priority": "low"},
]


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
    """Test/seed helper — same puts the flows perform (not used by runtime examples)."""
    from collections import Counter

    items = list(todos if todos is not None else SEED_TODO_ROWS)
    counts = Counter(str(t.get("priority") or "unknown") for t in items)
    rollup = [{"priority": k, "count": v} for k, v in counts.items()]
    return {
        "todo_rows": len(items),
        "priority_rows": len(rollup),
        "fact_put": providers.invoke("put-palm-todos", params={"value": items}),
        "view_put": providers.invoke(
            "put-palm-todos-by-priority", params={"value": rollup}
        ),
    }


__all__ = [
    "PALM_TODOS",
    "PALM_TODOS_BY_PRIORITY",
    "PUT_PALM_TODOS",
    "PUT_PALM_TODOS_BY_PRIORITY",
    "SEED_TODO_ROWS",
    "materialize_todo_analytics",
    "register_definitions",
]
