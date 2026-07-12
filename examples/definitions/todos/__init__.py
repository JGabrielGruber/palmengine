"""
Todos pack — definition-only durable list + analytics refresh.

Order: **resources → builder → analytics** (resource_ref by name).

Flows use resource + transform steps only (``count_by``, no commit hooks).

::

    palm flow start todo-builder
    # put-palm-todos → resource.changed → WorkIntent(todo-analytics)
    host.tick_work()   # 0.40.1 — run-when-able
    palm flow start todo-analytics
    # GET /analytics/ → palm-todos · palm-todos-by-priority
"""

from __future__ import annotations

from . import analytics, builder, dashboard, resources

__all__ = [
    "analytics",
    "builder",
    "dashboard",
    "resources",
    "register_definitions",
]


def register_definitions(repository: object) -> None:
    resources.register_definitions(repository)
    builder.register_definitions(repository)
    analytics.register_definitions(repository)
    dashboard.register_definitions(repository)
