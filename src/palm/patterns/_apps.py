"""
Django-style autoloading for pattern apps.

Each entry in ``INSTALLED_PATTERNS`` is a self-contained subpackage that
registers itself via ``registry.py`` on import.
"""

from __future__ import annotations

import importlib

INSTALLED_PATTERNS: tuple[str, ...] = ("dag", "etl", "wizard")


def autoload() -> None:
    """Import all installed pattern apps (triggers registry side effects)."""
    for name in INSTALLED_PATTERNS:
        importlib.import_module(f"palm.patterns.{name}")