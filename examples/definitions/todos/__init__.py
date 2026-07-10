"""
Todos pack — definition-only durable list + analytics refresh.

Order: **resources → builder → analytics** (resource_ref by name).

Flows use resource + transform steps only (``count_by``, no commit hooks).

::

    palm flow start todo-builder
    palm flow start todo-analytics
    # GET /analytics/ → palm-todos · palm-todos-by-priority
"""

from __future__ import annotations

from . import analytics, builder, resources

__all__ = [
    "analytics",
    "builder",
    "resources",
    "register_definitions",
]


def register_definitions(repository: object) -> None:
    resources.register_definitions(repository)
    builder.register_definitions(repository)
    analytics.register_definitions(repository)
