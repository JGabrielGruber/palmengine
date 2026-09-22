"""Catalog of real WorkloadRuntime packages.

``INSTALLED_RUNNERS`` lists packages that exist. The composition record names
which ones the install stroke imports (0.72.3). Listing ``host`` here does not
import it. The engine flag ``workload_host_enabled`` still starts that runtime
disabled when the record did install it.
"""

from __future__ import annotations

import importlib

INSTALLED_RUNNERS: tuple[str, ...] = (
    "local",  # Palm-managed process runner (trusted default)
    "host",  # full-machine subprocess; engine starts it disabled
    "neonroot",  # hermetic spawn via NeonRoot CLI
)


def autoload(names: tuple[str, ...]) -> None:
    """Import the named runner packages (triggers registry side effects)."""
    for name in names:
        importlib.import_module(f"plugins.runners.{name}")


__all__ = ["INSTALLED_RUNNERS", "autoload"]
