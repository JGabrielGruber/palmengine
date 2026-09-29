"""
Concrete behavior patterns (Django-style apps).

Catalog: dag, parallel, pipeline, wizard.
Intention stubs (etl) stay off that catalog (ST-003 / SD-013).

``autoload`` does not import a pattern. Import the pattern module to register it.
"""

from plugins.patterns._apps import (
    INSTALLED_PATTERNS,
    INTENTION_PATTERNS,
    autoload,
)

__all__ = [
    "INSTALLED_PATTERNS",
    "INTENTION_PATTERNS",
    "autoload",
]
