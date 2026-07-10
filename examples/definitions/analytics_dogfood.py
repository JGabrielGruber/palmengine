"""
Palm analytics dogfood (0.35) — **not** business/sales BI.

Canonical path: **todo-builder** (interact) → kv → published datasets → AnalyticsService
/ ``/analytics/``. Refresh via **todo-analytics** flow.

This module re-exports todo materialize helpers for tests and seeds.
"""

from __future__ import annotations

from examples.definitions.todo_resources import (
    PALM_TODOS,
    PALM_TODOS_BY_PRIORITY,
    SEED_TODO_ROWS,
    materialize_todo_analytics,
    register_definitions as register_todo_resources,
)

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
