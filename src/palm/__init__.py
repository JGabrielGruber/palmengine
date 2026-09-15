"""
Palm Engine — lightweight orchestration for multi-step transactional workflows.

The ``palm`` package is organized in layers:

- ``palm.app`` — :class:`~palm.app.host.ApplicationHost` (recommended), :class:`~palm.app.PalmKernel` (infra)
- ``palm.core`` — pure foundational engines (no imports from outside core)
- ``palm.system`` — system instance, ports, planes (:class:`~palm.system.runtime.base.BaseRuntime`, ExecutionPort)
- ``palm.common`` — shared libraries; residual executions/hooks/server kit; prefer palm.system for runtime/planes/executions
- ``palm.instances`` — durable process instance snapshots
- ``palm.patterns`` / ``palm.providers`` / ``palm.storages`` — extensible plugin apps (truthful install sets)
- ``palm.definitions`` — flow and process definition models
- ``palm.runtimes`` — CLI, embedded, server, and daemon surfaces

Public API version: ``palm.__version__`` (currently 0.68.0).

PyPI distribution name: ``palmengine`` (``pip install palmengine``).
"""

from __future__ import annotations

__version__ = "0.68.0"

__all__ = ["__version__"]
