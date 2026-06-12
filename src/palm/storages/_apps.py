"""
Django-style autoloading for storage apps.
"""

from __future__ import annotations

import importlib

CORE_STORAGES: tuple[str, ...] = ("memory", "filesystem")
OPTIONAL_STORAGES: tuple[str, ...] = ("postgres", "mongodb")
INSTALLED_STORAGES: tuple[str, ...] = CORE_STORAGES + OPTIONAL_STORAGES


def autoload(*, include_optional: bool = False) -> None:
    """Import core storage apps; optional backends load lazily via StorageFactory."""
    for name in CORE_STORAGES:
        importlib.import_module(f"palm.storages.{name}")
    if include_optional:
        for name in OPTIONAL_STORAGES:
            importlib.import_module(f"palm.storages.{name}")
