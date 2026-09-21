"""
Service domain bootstrap.

``INSTALLED_SERVICES`` is the catalog of real service packages.
The composition record's ``services`` tuple is the set the host walks (0.72.4).
``HostServiceRegistry`` builds that same tuple. This function imports the packages.
"""

from __future__ import annotations

import importlib

INSTALLED_SERVICES: tuple[str, ...] = (
    "definitions",
    "design",
    "execution",
    "inspect",
    "session",
    "assist",
)


def autoload(names: tuple[str, ...]) -> None:
    """Import the named service packages."""
    for name in names:
        importlib.import_module(f"palm.services.{name}")


__all__ = ["INSTALLED_SERVICES", "autoload"]
