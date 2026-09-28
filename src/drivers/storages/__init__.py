"""
Concrete storage backends — memory, postgres, mongodb, filesystem (Django-style apps).

Each subpackage registers via its own ``registry.py``. The composition record
names which backends :func:`autoload` imports
(:func:`palm.common.plugins.ensure_core_plugins`). Optional backends register
on demand through :func:`drivers.storages.load.ensure_registered`.
"""

from drivers.storages._apps import CORE_STORAGES, INSTALLED_STORAGES, OPTIONAL_STORAGES, autoload
from drivers.storages.load import ensure_registered, initialize_engine, open_backend

__all__ = [
    "CORE_STORAGES",
    "INSTALLED_STORAGES",
    "OPTIONAL_STORAGES",
    "autoload",
    "ensure_registered",
    "initialize_engine",
    "open_backend",
]
