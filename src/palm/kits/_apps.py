"""
Django-style autoloading for kits.

Each entry in ``INSTALLED_KITS`` is a real, importable kit package under
``palm.kits.<name>``. Intentions (future kits without implementation) stay off
this list so doctor and inventory stay honest.

``CORE_KITS`` are loaded by :func:`autoload` at bootstrap. Surface kit
``server`` stays on the install list but registers when
:mod:`palm.runtimes.server` (or :mod:`palm.kits.server`) is imported — so an
embedded ApplicationHost does not pull the server kit (0.71.21).
"""

from __future__ import annotations

import importlib

# Real kits only — ship when purpose and package exist.
INSTALLED_KITS: tuple[str, ...] = (
    "server",
    "present",
    "authoring",
)

# Bootstrap autoload — not the HTTP surface kit.
CORE_KITS: tuple[str, ...] = (
    "present",
    "authoring",
)

# Named futures without a body (do not auto-load; purpose lives in STUBS/VISION).
INTENTION_KITS: tuple[str, ...] = ()


def autoload() -> None:
    """Import core kits and register them on the kit registry."""
    for name in CORE_KITS:
        importlib.import_module(f"palm.kits.{name}")


__all__ = ["CORE_KITS", "INSTALLED_KITS", "INTENTION_KITS", "autoload"]
