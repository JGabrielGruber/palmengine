"""
Concrete storage backends — memory, postgres, mongodb, filesystem (Django-style apps).

Each subpackage registers via its own ``registry.py``.
"""

from palm.storages._apps import INSTALLED_STORAGES, autoload

autoload()

from palm.storages import filesystem, memory, mongodb, postgres  # noqa: E402

__all__ = ["INSTALLED_STORAGES", "autoload", "filesystem", "memory", "mongodb", "postgres"]