"""
System start phase: storage select (system.storage.select).

Subject: shell storage seat + StorageFactory.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.common.storage import StorageFactory
from palm.system.boot.context import BootContext
from palm.system.boot.definition import PhaseDefinition
from palm.system.boot.shell import resolve_shell


def select_system_storage(
    shell: Any,
    options: Mapping[str, Any] | None = None,
) -> Any:
    """Initialize storage on *shell* when not already initialized."""
    opts = dict(options or {})
    if not shell.storage.is_initialized:
        backend = opts.get("storage_backend")
        if not isinstance(backend, str) or not backend.strip():
            raise RuntimeError(
                "system.storage.select: storage_backend is required. "
                "The application names a storage plugin it has registered."
            )
        StorageFactory.initialize_engine(
            shell.storage,
            storage_backend=backend.strip(),
            **dict(opts.get("backend_options") or {}),
        )
    return shell.storage


def run(ctx: BootContext, options: Mapping[str, Any]) -> None:
    storage = select_system_storage(resolve_shell(ctx), options)
    ctx.publish(storage=storage)


DEFINITION = PhaseDefinition(
    id="system.storage.select",
    run=run,
    description="Select the storage backend the application named",
)

__all__ = ["DEFINITION", "run", "select_system_storage"]
