"""
Palm Engine — lightweight orchestration for multi-step transactional workflows.

The ``palm`` package is organized in layers:

- ``palm.app`` — :class:`~palm.app.host.ApplicationHost` (recommended), :class:`~palm.app.PalmApp` (infra)
- ``palm.core`` — pure foundational engines (no imports from outside core)
- ``palm.common`` — shared coordination (plans, submission, hooks, persistence)
- ``palm.instances`` — durable process instance snapshots
- ``palm.patterns`` / ``palm.providers`` / ``palm.storages`` — extensible plugin apps
- ``palm.definitions`` — flow and process definition models
- ``palm.runtimes`` — CLI, embedded, server, and daemon surfaces

Public API version: ``palm.__version__`` (currently 0.21.9).

PyPI distribution name: ``palmengine`` (``pip install palmengine``).
"""

from __future__ import annotations

__version__ = "0.21.9"

__all__ = ["__version__"]
