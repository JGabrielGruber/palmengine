"""
Concrete behavior patterns (Django-style apps).

Catalog: dag, parallel, pipeline, wizard.
Intention stubs (etl) stay off that catalog (ST-003 / SD-013).

The composition record names which patterns :func:`autoload` imports
(:func:`palm.common.plugins.ensure_core_plugins`), not package import.
"""

from palm.patterns._apps import (
    INSTALLED_PATTERNS,
    INTENTION_PATTERNS,
    autoload,
)

__all__ = [
    "INSTALLED_PATTERNS",
    "INTENTION_PATTERNS",
    "autoload",
]
