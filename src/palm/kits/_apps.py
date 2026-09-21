"""
Django-style autoloading for kits.

Each entry in ``INSTALLED_KITS`` is a real, importable kit package under
``palm.kits.<name>``. Intentions (future kits without implementation) stay off
this list so doctor and inventory stay honest.

``INSTALLED_KITS`` is the catalog. The composition record names which kits
the install stroke imports (0.72.3). Surface kit ``server`` is on the catalog.
Saved records do not name it, so an embedded host does not pull it (0.71.21).
The server runtime imports :mod:`palm.kits.server` when that surface starts.
"""

from __future__ import annotations

import importlib

# Real kits only — ship when purpose and package exist.
INSTALLED_KITS: tuple[str, ...] = (
    "server",
    "present",
    "authoring",
)

# Named futures without a body (do not auto-load; purpose lives in STUBS/VISION).
INTENTION_KITS: tuple[str, ...] = ()


def autoload(names: tuple[str, ...]) -> None:
    """Import the named kits and register them on the kit registry."""
    for name in names:
        importlib.import_module(f"palm.kits.{name}")


__all__ = ["INSTALLED_KITS", "INTENTION_KITS", "autoload"]
