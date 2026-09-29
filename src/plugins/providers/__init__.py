"""
Concrete resource providers (Django-style apps).

Catalog: rest, palm, kv, file, authoring. Intention stubs
(graphql, postgres) are packages only — not on the catalog (ST-001 / SD-013).

``autoload`` does not import a provider. Import the provider module to register it.
"""

from plugins.providers._apps import (
    INSTALLED_PROVIDERS,
    INTENTION_PROVIDERS,
    autoload,
)

__all__ = [
    "INSTALLED_PROVIDERS",
    "INTENTION_PROVIDERS",
    "autoload",
]
