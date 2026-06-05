"""
Palm Engine — lightweight orchestration for multi-step transactional workflows.

The ``palm`` package is organized in layers:

- ``palm.core`` — pure foundational engines (no imports from outside core)
- ``palm.patterns`` / ``palm.providers`` / ``palm.storages`` — concrete implementations
- ``palm.definitions`` — flow and process definitions
- ``palm.runtimes`` — execution surfaces (CLI, server, daemon, embedded)
"""

from __future__ import annotations

__version__ = "0.4.0-dev"

__all__ = ["__version__"]
