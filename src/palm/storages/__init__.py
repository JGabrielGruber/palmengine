"""
Concrete storage backends — memory, postgres, mongodb, filesystem (Django-style apps).

Each subpackage registers via its own ``registry.py``. Core backends autoload at
import; optional backends register lazily through :class:`~palm.common.storage.StorageFactory`.
"""

from palm.storages._apps import CORE_STORAGES, INSTALLED_STORAGES, OPTIONAL_STORAGES, autoload

autoload()

from palm.storages import filesystem, memory  # noqa: E402

__all__ = [
    "CORE_STORAGES",
    "INSTALLED_STORAGES",
    "OPTIONAL_STORAGES",
    "autoload",
    "filesystem",
    "memory",
]