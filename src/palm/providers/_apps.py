"""
Django-style autoloading for provider apps.
"""

from __future__ import annotations

import importlib

INSTALLED_PROVIDERS: tuple[str, ...] = ("rest", "graphql", "postgres")


def autoload() -> None:
    for name in INSTALLED_PROVIDERS:
        importlib.import_module(f"palm.providers.{name}")