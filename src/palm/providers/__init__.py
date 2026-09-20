"""
Concrete resource providers (Django-style apps).

Default install is truthful: rest, palm, kv, file, authoring. Intention stubs
(graphql, postgres) are packages only — not auto-loaded (ST-001 / SD-013).

Registries populate via :func:`autoload` at bootstrap
(:func:`palm.common.plugins.ensure_core_plugins`), not on package import.
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
