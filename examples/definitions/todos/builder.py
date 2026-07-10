"""
Todo builder — **definition-only** persist path.

After the collection step, the wizard:

1. ``count_by`` priority → ``todos_by_priority``
2. ``put-palm-todos`` (resource) from ``state.todos``
3. ``put-palm-todos-by-priority`` from ``state.todos_by_priority``

No commit hooks. Same pattern as coconut resource steps.

::

    palm flow start todo-builder
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

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
        "include_commit": False,
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "intro",
                "title": "Welcome",
                "prompt": (
                    "Build a todo list. On finish, Palm runs transform + resource "
                    "steps to persist kv facts for Analytics (palm-todos)."
                ),
                "step_kind": "introduction",
                "required": False,
            },
            {
                "slug": "todos",
                "title": "Todo List",
                "prompt": (
                    "Manage your todos — add items, edit/remove, then continue."
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
            {
                "slug": "rollup_priority",
                "title": "Roll up by priority",
                "prompt": "count_by priority → todos_by_priority",
                "step_kind": "transform",
                "source_key": "todos",
                "target_key": "todos_by_priority",
                "rule": "count_by",
                "options": {"field": "priority"},
            },
            {
                "slug": "save_todos",
                "title": "Save todos",
                "prompt": "Persist list to kv (put-palm-todos)",
                "step_kind": "resource",
                "resource_ref": "put-palm-todos",
            },
            {
                "slug": "save_priority_view",
                "title": "Save priority view",
                "prompt": "Persist rollup to kv (put-palm-todos-by-priority)",
                "step_kind": "resource",
                "resource_ref": "put-palm-todos-by-priority",
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
        "description": "Todo collection + definition-only kv/analytics publish",
    },
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(TODO_BUILDER_FLOW)
    if callable(save_process):
        save_process(TODO_BUILDER_PROCESS)


__all__ = [
    "TODO_BUILDER_FLOW",
    "TODO_BUILDER_PROCESS",
    "TODO_ITEM_SCHEMA",
    "register_definitions",
]
