"""
Django-style autoloading for kits.

Each entry in ``INSTALLED_KITS`` is a real, importable kit package under
``palm.kits.<name>``. Intentions (future kits without implementation) stay off
this list so doctor and inventory stay honest.

``INSTALLED_KITS`` names packages that exist. ``autoload`` does not import them.
Import the kit module to register it.
"""

from __future__ import annotations

# Real kits only — ship when purpose and package exist.
INSTALLED_KITS: tuple[str, ...] = (
    "server",
    "present",
    "authoring",
)

# Named futures without a body (do not auto-load; purpose lives in STUBS/VISION).
INTENTION_KITS: tuple[str, ...] = ()


def autoload(names: tuple[str, ...]) -> None:
    """Refuse a catalog import. Import the kit module that registers the name."""
    if names:
        joined = ", ".join(names)
        raise RuntimeError(
            f"catalog autoload is withdrawn; import the module that registers: {joined}"
        )


__all__ = ["INSTALLED_KITS", "INTENTION_KITS", "autoload"]
