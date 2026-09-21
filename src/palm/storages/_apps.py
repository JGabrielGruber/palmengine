"""
Django-style catalog for storage apps.

``CORE_STORAGES`` and ``OPTIONAL_STORAGES`` list real backends.
The composition record names which ones the install stroke imports (0.72.3).
``postgres`` and ``mongodb`` stay off the saved records. ``StorageFactory``
still loads an optional backend on demand.
"""

from __future__ import annotations

import importlib

CORE_STORAGES: tuple[str, ...] = ("memory", "filesystem")
# Intention backends (ST-002) — load only via StorageFactory / explicit opt-in.
OPTIONAL_STORAGES: tuple[str, ...] = ("postgres", "mongodb")
# Truthful default install = core only (not optional placeholders).
INSTALLED_STORAGES: tuple[str, ...] = CORE_STORAGES


def autoload(names: tuple[str, ...]) -> None:
    """Import the named storage apps (triggers registry side effects)."""
    for name in names:
        importlib.import_module(f"palm.storages.{name}")
