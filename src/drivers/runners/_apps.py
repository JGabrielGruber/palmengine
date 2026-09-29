"""Catalog of real WorkloadRuntime packages.

``INSTALLED_RUNNERS`` names packages that exist. ``autoload`` does not import them.
Import the runner module to register it.
"""

from __future__ import annotations

INSTALLED_RUNNERS: tuple[str, ...] = (
    "local",  # Palm-managed process runner (trusted default)
    "host",  # full-machine subprocess; engine starts it disabled
    "neonroot",  # hermetic spawn via NeonRoot CLI
)


def autoload(names: tuple[str, ...]) -> None:
    """Refuse a catalog import. Import the runner module that registers the name."""
    if names:
        joined = ", ".join(names)
        raise RuntimeError(
            f"catalog autoload is withdrawn; import the module that registers: {joined}"
        )


__all__ = ["INSTALLED_RUNNERS", "autoload"]
