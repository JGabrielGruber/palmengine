"""
Todo analytics interaction flow (0.35 dogfood).

Resources alone are not the product — this wizard **loads** stored todos and
**rebuilds** the priority view so operators exercise definitions end-to-end:

1. Load ``palm-todos`` (resource step)
2. Confirm rebuild of ``palm-todos-by-priority``
3. Commit writes the view (and re-puts fact)

```bash
palm flow start todo-analytics
# /analytics/ → palm-todos · palm-todos-by-priority
```
"""

from __future__ import annotations

from typing import Any

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.patterns.wizard.bindings.compensation.handler import (
    CommitResult,
    default_commit_registry,
)

import importlib.util
import sys
from pathlib import Path


def _import_sibling(stem: str):
    path = Path(__file__).resolve().parent / f"{stem}.py"
    name = f"palm_example_definitions_{stem}"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_todo_resources = _import_sibling("todo_resources")
priority_rollup = _todo_resources.priority_rollup
register_todo_resources = _todo_resources.register_definitions

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
    # Provider envelope shapes: value.items or items after binding
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
    register_todo_resources(repository)
    default_commit_registry().register(
        "rebuild_todo_analytics", _rebuild_todo_analytics
    )
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(TODO_ANALYTICS_FLOW)
    if callable(save_process):
        save_process(TODO_ANALYTICS_PROCESS)
