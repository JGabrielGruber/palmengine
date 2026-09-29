"""
Django-style catalog for storage apps.

``CORE_STORAGES`` and ``OPTIONAL_STORAGES`` name real backends.
``autoload`` does not import them. ``drivers.storages.load`` opens a backend by name.
"""

from __future__ import annotations

CORE_STORAGES: tuple[str, ...] = ("memory", "filesystem")
# Intention backends (ST-002) — load only via drivers.storages.load / explicit opt-in.
OPTIONAL_STORAGES: tuple[str, ...] = ("postgres", "mongodb")
# Truthful default install = core only (not optional placeholders).
INSTALLED_STORAGES: tuple[str, ...] = CORE_STORAGES


def autoload(names: tuple[str, ...]) -> None:
    """Refuse a catalog import. Open a backend through ``drivers.storages.load``."""
    if names:
        joined = ", ".join(names)
        raise RuntimeError(
            f"catalog autoload is withdrawn; import the module that registers: {joined}"
        )
