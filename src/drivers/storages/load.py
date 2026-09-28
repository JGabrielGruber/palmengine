"""Load a storage backend by name.

The module map lives here. ``palm.system`` does not import this module.
Callers that need a backend import ``drivers.storages``.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from palm.core.exceptions import ConfigurationError, RegistryError
from palm.core.registry import storage_registry
from palm.core.storage import BaseBackend, StorageEngine

_OPTIONAL_STORAGES: dict[str, str] = {
    "postgres": "postgres",
    "mongodb": "mongodb",
}
_STORAGE_MODULES: dict[str, str] = {
    "memory": "drivers.storages.memory",
    "filesystem": "drivers.storages.filesystem",
    "postgres": "drivers.storages.postgres",
    "mongodb": "drivers.storages.mongodb",
}


def ensure_registered(name: str) -> None:
    """Import the storage module so its backend is registered."""
    normalized = name.strip().lower()
    if normalized in storage_registry.names():
        return
    module_path = _STORAGE_MODULES.get(normalized)
    if module_path is None:
        raise RegistryError(
            f"Unknown storage backend {name!r}. Available modules: {sorted(_STORAGE_MODULES)}"
        )
    try:
        importlib.import_module(module_path)
    except ImportError as exc:
        extra = _OPTIONAL_STORAGES.get(normalized)
        if extra is not None:
            raise ConfigurationError(
                f"Storage backend {name!r} requires optional dependencies. "
                f"Install with: pip install palmengine[{extra}]"
            ) from exc
        raise ConfigurationError(
            f"Failed to import storage backend {name!r} from {module_path}: {exc}"
        ) from exc
    if normalized not in storage_registry.names():
        raise ConfigurationError(
            f"Storage module {module_path!r} did not register backend {normalized!r}"
        )


def open_backend(name: str, **options: Any) -> BaseBackend:
    """Register ``name``, construct the backend, and open it."""
    normalized = name.strip().lower()
    ensure_registered(normalized)
    backend = storage_registry.get(normalized)(name=normalized, **options)
    backend.open()
    return backend


def initialize_engine(
    engine: StorageEngine,
    *,
    storage_backend: str = "memory",
    data_dir: Path | None = None,
    settings: Any | None = None,
    **backend_options: Any,
) -> StorageEngine:
    """Open ``storage_backend`` on ``engine``.

    This is the driver-package loader. System start does not call it.
    """
    from palm.common.storage import StorageFactory

    if settings is not None:
        storage_backend = str(getattr(settings, "storage_backend", storage_backend))
        data_dir = getattr(settings, "data_dir", data_dir)
    backend = storage_backend.strip().lower()
    ensure_registered(backend)
    options = StorageFactory.backend_options(
        storage_backend=backend,
        data_dir=data_dir,
        **backend_options,
    )
    engine.initialize(backend=backend, backend_options=options)
    return engine


__all__ = ["ensure_registered", "initialize_engine", "open_backend"]
