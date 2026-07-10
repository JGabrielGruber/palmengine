"""
Todo analytics refresh — **definition-only** flow (no Python rebuild hook).

1. Load ``palm-todos``
2. Extract list (``jsonpath_extract`` path=value)
3. ``count_by`` priority
4. Put ``put-palm-todos-by-priority``

::

    palm flow start todo-analytics
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

TODO_ANALYTICS_FLOW = FlowDefinition(
    id="flow-todo-analytics",
    name="todo-analytics",
    pattern="wizard",
    options={
        "include_summary": True,
        "include_commit": False,
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "intro",
                "title": "Refresh todo analytics",
                "prompt": (
                    "Palm dogfood — reload stored todos and rebuild the published "
                    "priority view with transform count_by + resource put "
                    "(no custom commit code)."
                ),
                "step_kind": "introduction",
                "required": False,
            },
            {
                "slug": "load_todos",
                "title": "Load palm-todos",
                "prompt": "kv get → todo_payload",
                "step_kind": "resource",
                "resource_ref": "palm-todos",
                "output_key": "todo_payload",
            },
            {
                "slug": "extract_items",
                "title": "Extract todo rows",
                "prompt": "jsonpath_extract value → todos",
                "step_kind": "transform",
                "source_key": "todo_payload",
                "target_key": "todos",
                "rule": "jsonpath_extract",
                "options": {"path": "value", "default": []},
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
                "slug": "save_priority_view",
                "title": "Save priority view",
                "prompt": "put-palm-todos-by-priority",
                "step_kind": "resource",
                "resource_ref": "put-palm-todos-by-priority",
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
        "description": "Definition-only rebuild of palm-todos-by-priority",
    },
)


def register_definitions(repository: object) -> None:
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
