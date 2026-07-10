"""
Todo analytics — optional operator inspect of stored palm-todos.

Priority rollup is a **virtual** analytics view (no rebuild flow required).

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
                "title": "Todo analytics",
                "prompt": (
                    "Load stored todos for inspection. Priority counts are computed "
                    "virtually via Analytics (palm-todos-by-priority) — no second put."
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
        ],
    },
)

TODO_ANALYTICS_PROCESS = ProcessDefinition(
    id="proc-todo-analytics",
    name="todo-analytics-process",
    flows=[TODO_ANALYTICS_FLOW],
    metadata={
        "example": True,
        "description": "Inspect palm-todos; virtual priority view via Analytics",
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
