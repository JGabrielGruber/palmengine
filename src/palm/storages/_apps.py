"""
Django-style autoloading for storage apps.
"""

from __future__ import annotations

import importlib

INSTALLED_STORAGES: tuple[str, ...] = ("memory", "postgres", "mongodb", "filesystem")


def autoload() -> None:
    for name in INSTALLED_STORAGES:
        importlib.import_module(f"palm.storages.{name}")