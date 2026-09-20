"""
Concrete behavior patterns (Django-style apps).

Default install is truthful: dag, parallel, pipeline, wizard.
Intention stubs (etl) are not auto-loaded (ST-003 / SD-013).

Registries populate via :func:`autoload` at bootstrap
(:func:`palm.common.plugins.ensure_core_plugins`), not on package import.
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
