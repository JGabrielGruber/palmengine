"""
Service domain bootstrap.

Domain modules register REST/MCP entries via per-package ``registry.py`` (0.16b+).
"""

from __future__ import annotations

INSTALLED_SERVICES: tuple[str, ...] = (
    "definitions",
    "execution",
    "system",
    "assist",
)


def autoload() -> None:
    """Import installed service packages."""
    import importlib

    for name in INSTALLED_SERVICES:
        importlib.import_module(f"palm.services.{name}")


__all__ = ["INSTALLED_SERVICES", "autoload"]