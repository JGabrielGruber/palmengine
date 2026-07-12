"""
Todo analytics — optional operator inspect of stored palm-todos.

Priority rollup is a **virtual** analytics view (no rebuild flow required).

::

    palm flow start todo-analytics
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

# 0.40.1 — on put of the list (write resource used by todo-builder), enqueue this flow.
# Host: resource.changed → WorkIntent → tick_work() runs when able.
_TODO_ANALYTICS_TRIGGERS = [
    {
        "kind": "on_resource",
        "resource": "put-palm-todos",
        "actions": ["put"],
        "debounce": 2.0,
        "work": {
            "flow_id": "todo-analytics",
            "coalesce_key": "on_resource:put-palm-todos:todo-analytics",
        },
    },
    # Alias if invoke uses the published fact ref with a put action
    {
        "kind": "on_resource",
        "resource": "palm-todos",
        "actions": ["put"],
        "debounce": 2.0,
        "work": {
            "flow_id": "todo-analytics",
            "coalesce_key": "on_resource:palm-todos:todo-analytics",
        },
    },
]

TODO_ANALYTICS_FLOW = FlowDefinition(
    id="flow-todo-analytics",
    name="todo-analytics",
    pattern="wizard",
    options={
        "include_summary": True,
        "include_commit": False,
        "allow_backtrack": True,
        # FlowDefinition has no top-level metadata; triggers live in options (host parses options).
        "triggers": _TODO_ANALYTICS_TRIGGERS,
        "steps": [
            {
                "slug": "intro",
                "title": "Todo analytics",
                "prompt": (
                    "Load stored todos for inspection. Priority counts are computed "
                    "virtually via Analytics (palm-todos-by-priority) — no second put. "
                    "Auto-enqueued after put-palm-todos (0.40.1); host.tick_work() runs it."
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
        "triggers": _TODO_ANALYTICS_TRIGGERS,
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
