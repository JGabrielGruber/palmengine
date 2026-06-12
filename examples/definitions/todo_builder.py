"""
Todo list builder wizard — collection steps, schemas, and scoped item editing.

Demonstrates Phase 5+ state capabilities:

- **Collection step** — add, edit, and remove repeatable todo items
- **Per-item scopes** — each field edits under ``todos > item-N > field``
- **Per-field schemas** — title, optional due date, priority enum
- **Flow schema** — validates the full ``todos`` array at summary/commit
- **Resume** — collection phase, draft, and list preserved in snapshots

```bash
palm flow start todo-builder
```
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.patterns.wizard.handler import CommitResult, default_commit_registry

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
                    "then review everything before saving."
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
        "description": "Dynamic todo list wizard with collection steps and schemas",
    },
)


def _persist_todo_list(ctx: object) -> CommitResult:
    answers = getattr(ctx, "answers", {})
    todos = answers.get("todos")
    if not isinstance(todos, list) or not todos:
        return CommitResult.failure("Todo list is empty")
    return CommitResult.success({"todos": todos, "count": len(todos)})


def register_definitions(repository: object) -> None:
    default_commit_registry().register("persist_todo_list", _persist_todo_list)
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(TODO_BUILDER_FLOW)
    if callable(save_process):
        save_process(TODO_BUILDER_PROCESS)