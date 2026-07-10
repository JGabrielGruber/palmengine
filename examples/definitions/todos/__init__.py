"""
Todos example pack — durable list wizard + Palm analytics dogfood.

Registration order:

1. **resources** — kv put/get + published analytics datasets  
2. **builder** — ``todo-builder`` flow (commit → persist)  
3. **analytics** — ``todo-analytics`` flow (load + rebuild views)

::

    palm flow start todo-builder
    palm flow start todo-analytics
    # GET /analytics/ → palm-todos, palm-todos-by-priority
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
    """Register todo resources, then builder, then analytics interaction flow."""
    resources.register_definitions(repository)
    builder.register_definitions(repository)
    analytics.register_definitions(repository)
