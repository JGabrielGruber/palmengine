"""
Concrete behavior patterns — wizard, DAG, and ETL (Django-style apps).

Each subpackage under ``palm.patterns`` is self-contained and registers via
its own ``registry.py``. Import this package (or call ``autoload()``) to wire
all installed apps.
"""

from palm.patterns._apps import INSTALLED_PATTERNS, autoload

autoload()

from palm.patterns import dag, etl, wizard  # noqa: E402

__all__ = ["INSTALLED_PATTERNS", "autoload", "dag", "etl", "wizard"]