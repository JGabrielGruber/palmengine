"""
Concrete storage backends — memory, postgres, mongodb, filesystem (Django-style apps).

Each subpackage registers via its own ``registry.py``. The composition record
names which backends :func:`autoload` imports
(:func:`palm.common.plugins.ensure_core_plugins`). Optional backends still
register on demand through :class:`~palm.common.storage.StorageFactory`.
"""

from palm.storages._apps import CORE_STORAGES, INSTALLED_STORAGES, OPTIONAL_STORAGES, autoload

__all__ = [
    "CORE_STORAGES",
    "INSTALLED_STORAGES",
    "OPTIONAL_STORAGES",
    "autoload",
]
