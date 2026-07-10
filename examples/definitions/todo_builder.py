"""
Todo list builder — collection wizard with **durable kv** + Palm analytics.

- Collection / schemas / resume (unchanged UX)
- Commit persists to ``put-palm-todos`` and rolls up ``put-palm-todos-by-priority``
- Published reads: ``palm-todos``, ``palm-todos-by-priority`` (AnalyticsService)

```bash
palm flow start todo-builder
# then: GET /analytics/ or analytics.query("palm-todos")
```
"""

from __future__ import annotations

from typing import Any

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.patterns.wizard.bindings.compensation.handler import (
    CommitResult,
    default_commit_registry,
)

from examples.definitions.todo_resources import (
    priority_rollup,
    register_definitions as register_todo_resources,
)

TODO_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "due_date": {"type": "string"},
        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["title", "priority"],
}

TODO_BUILDER_FLOW = FlowDefinition(
    id="flow-todo-builder",
    name="todo-builder",
    pattern="wizard",
    state_schema={
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "minItems": 1,
                "items": TODO_ITEM_SCHEMA,
            },
        },
        "required": ["todos"],
    },
    options={
        "include_summary": True,
        "include_commit": True,
        "commit_hook": "persist_todo_list",
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "intro",
                "title": "Welcome",
                "prompt": (
                    "Let's build your todo list. You'll add items one at a time, "
                    "then review everything before saving. "
                    "On commit, Palm persists the list to kv and refreshes "
                    "published analytics datasets (palm-todos)."
                ),
                "step_kind": "introduction",
                "required": False,
            },
            {
                "slug": "todos",
                "title": "Todo List",
                "prompt": (
                    "Manage your todos — add items, edit/remove by number or title "
                    "search, then continue."
                ),
                "step_kind": "collection",
                "collection_key": "todos",
                "label_field": "title",
                "min_items": 1,
                "item_fields": [
                    {
                        "slug": "title",
                        "title": "Title",
                        "prompt": "What needs to be done?",
                        "state_schema": {"type": "string", "minLength": 1},
                        "validation": [{"rule": "min_length", "params": {"min": 1}}],
                    },
                    {
                        "slug": "due_date",
                        "title": "Due Date",
                        "prompt": "Due date (YYYY-MM-DD, or leave empty to skip)",
                        "required": False,
                        "state_schema": {"type": ["string", "null"]},
                        "validation": [
                            {
                                "rule": "regex",
                                "params": {
                                    "pattern": r"^$|^\d{4}-\d{2}-\d{2}$",
                                    "message": "Use YYYY-MM-DD or leave empty",
                                },
                            }
                        ],
                    },
                    {
                        "slug": "priority",
                        "title": "Priority",
                        "prompt": "How urgent is this?",
                        "field_type": "choice",
                        "choices": ["low", "medium", "high"],
                        "state_schema": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                    },
                ],
            },
        ],
    },
)

TODO_BUILDER_PROCESS = ProcessDefinition(
    id="proc-todo-builder",
    name="todo-builder-process",
    flows=[TODO_BUILDER_FLOW],
    metadata={
        "example": True,
        "description": "Dynamic todo list with durable kv and Palm analytics",
    },
)


def _persist_todo_list(ctx: object) -> CommitResult:
    answers = getattr(ctx, "answers", {}) or {}
    todos = answers.get("todos")
    if not isinstance(todos, list) or not todos:
        return CommitResult.failure("Todo list is empty")

    items = [t for t in todos if isinstance(t, dict)]
    if not items:
        return CommitResult.failure("Todo list is empty")

    fact = {"items": items, "count": len(items)}
    view = {"items": priority_rollup(items)}
    engine = getattr(ctx, "resource_engine", None)
    persisted = False
    if engine is not None:
        if not getattr(engine, "is_initialized", False):
            engine.initialize()
        put_fact = engine.invoke("put-palm-todos", params={"value": fact})
        if not put_fact.success:
            return CommitResult.failure(
                put_fact.error or "Failed to persist todos to kv"
            )
        put_view = engine.invoke(
            "put-palm-todos-by-priority", params={"value": view}
        )
        if not put_view.success:
            return CommitResult.failure(
                put_view.error or "Failed to persist priority view"
            )
        persisted = True

    return CommitResult.success(
        {
            "todos": items,
            "count": len(items),
            "persisted": persisted,
            "analytics": {
                "datasets": ["palm-todos", "palm-todos-by-priority"],
                "priority_rollup": view["items"],
            },
        }
    )


def register_definitions(repository: object) -> None:
    register_todo_resources(repository)
    default_commit_registry().register("persist_todo_list", _persist_todo_list)
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(TODO_BUILDER_FLOW)
    if callable(save_process):
        save_process(TODO_BUILDER_PROCESS)
