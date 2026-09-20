"""
Concrete storage backends — memory, postgres, mongodb, filesystem (Django-style apps).

Each subpackage registers via its own ``registry.py``. Core backends load via
:func:`autoload` at bootstrap (:func:`palm.common.plugins.ensure_core_plugins`);
optional backends register lazily through :class:`~palm.common.storage.StorageFactory`.
"""

from palm.storages._apps import CORE_STORAGES, INSTALLED_STORAGES, OPTIONAL_STORAGES, autoload

__all__ = [
    "CORE_STORAGES",
    "INSTALLED_STORAGES",
    "OPTIONAL_STORAGES",
    "autoload",
]
