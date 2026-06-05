"""
Palm Engine — lightweight orchestration for multi-step transactional workflows.

The ``palm`` package is organized in layers:

- ``palm.core`` — pure foundational engines (no imports from outside core)
- ``palm.executions`` — submit/resume/build from definitions
- ``palm.instances`` — durable process instance snapshots
- ``palm.patterns`` / ``palm.providers`` / ``palm.storages`` — concrete implementations
- ``palm.definitions`` — flow and process definitions
- ``palm.runtimes`` — CLI, embedded, and future server/daemon surfaces

Public API version: ``palm.__version__`` (currently 0.5.0-dev).
"""

from __future__ import annotations

__version__ = "0.5.0-dev"

__all__ = ["__version__"]
