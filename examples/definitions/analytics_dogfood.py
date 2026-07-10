"""
Palm analytics dogfood (0.35) — **not** business/sales BI.

Canonical path: **todo-builder** (interact) → kv → published datasets → AnalyticsService
/ ``/analytics/``. Refresh via **todo-analytics** flow.

This module re-exports todo materialize helpers for tests and seeds.
"""

from __future__ import annotations

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
PALM_TODOS = _todo_resources.PALM_TODOS
PALM_TODOS_BY_PRIORITY = _todo_resources.PALM_TODOS_BY_PRIORITY
SEED_TODO_ROWS = _todo_resources.SEED_TODO_ROWS
materialize_todo_analytics = _todo_resources.materialize_todo_analytics
register_todo_resources = _todo_resources.register_definitions

# Back-compat names for early 0.35.5 tests / docs
materialize_analytics_dogfood = materialize_todo_analytics
SEED_SALES_ROWS = SEED_TODO_ROWS  # deprecated alias — Palm todos, not sales


def register_definitions(repository: object) -> None:
    """Register Palm todo analytics resources (flows register via todo_* modules)."""
    register_todo_resources(repository)


__all__ = [
    "PALM_TODOS",
    "PALM_TODOS_BY_PRIORITY",
    "SEED_TODO_ROWS",
    "SEED_SALES_ROWS",
    "materialize_analytics_dogfood",
    "materialize_todo_analytics",
    "register_definitions",
]
