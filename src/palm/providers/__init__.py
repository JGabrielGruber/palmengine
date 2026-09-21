"""
Concrete resource providers (Django-style apps).

Catalog: rest, palm, kv, file, authoring. Intention stubs
(graphql, postgres) are packages only — not on the catalog (ST-001 / SD-013).

The composition record names which providers :func:`autoload` imports
(:func:`palm.common.plugins.ensure_core_plugins`), not package import.
"""

from palm.providers._apps import (
    INSTALLED_PROVIDERS,
    INTENTION_PROVIDERS,
    autoload,
)

__all__ = [
    "INSTALLED_PROVIDERS",
    "INTENTION_PROVIDERS",
    "autoload",
]
