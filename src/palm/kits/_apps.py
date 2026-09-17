"""
Django-style autoloading for kits.

Each entry in ``INSTALLED_KITS`` is a real, importable kit package under
``palm.kits.<name>``. Intentions (future kits without implementation) stay off
this list so doctor and inventory stay honest.
"""

from __future__ import annotations

import importlib

# Real kits only — ship when purpose and package exist.
INSTALLED_KITS: tuple[str, ...] = (
    "server",
    "present",
)

# Named futures without a body (do not auto-load; purpose lives in STUBS/VISION).
INTENTION_KITS: tuple[str, ...] = ()


def autoload() -> None:
    """Import installed kits and register them on the kit registry."""
    for name in INSTALLED_KITS:
        importlib.import_module(f"palm.kits.{name}")


__all__ = ["INSTALLED_KITS", "INTENTION_KITS", "autoload"]
