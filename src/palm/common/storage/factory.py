"""
StorageFactory — lazy backend registration and PalmSettings integration.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from palm.core.exceptions import ConfigurationError, RegistryError
from palm.core.registry import storage_registry
from palm.core.storage import BaseBackend, StorageEngine

_CORE_STORAGES: tuple[str, ...] = ("memory", "filesystem")
_OPTIONAL_STORAGES: dict[str, str] = {
    "postgres": "postgres",
    "mongodb": "mongodb",
}
_STORAGE_MODULES: dict[str, str] = {
    "memory": "palm.storages.memory",
    "filesystem": "palm.storages.filesystem",
    "postgres": "palm.storages.postgres",
    "mongodb": "palm.storages.mongodb",
}
_DEFAULT_DATA_DIR = Path("data")


class StorageFactory:
    """
    Resolve storage backends by name with lazy module loading.

    Core backends (``memory``, ``filesystem``) ship with Palm. Optional
    backends declare a uv extra; missing extras raise :class:`~palm.core.exceptions.ConfigurationError`
    with install guidance instead of an opaque import error.
    """

    @staticmethod
    def ensure_registered(name: str) -> None:
        """Import the storage app module so its backend is registered."""
        normalized = name.strip().lower()
        if normalized in storage_registry.names():
            return
        module_path = _STORAGE_MODULES.get(normalized)
        if module_path is None:
            raise RegistryError(
                f"Unknown storage backend {name!r}. "
                f"Available modules: {sorted(_STORAGE_MODULES)}"
            )
        try:
            importlib.import_module(module_path)
        except ImportError as exc:
            extra = _OPTIONAL_STORAGES.get(normalized)
            if extra is not None:
                raise ConfigurationError(
                    f"Storage backend {name!r} requires optional dependencies. "
                    f"Install with: uv sync --extra {extra}"
                ) from exc
            raise ConfigurationError(
                f"Failed to import storage backend {name!r} from {module_path}: {exc}"
            ) from exc
        if normalized not in storage_registry.names():
            raise ConfigurationError(
                f"Storage module {module_path!r} did not register backend {normalized!r}"
            )

    @staticmethod
    def resolve_data_dir(data_dir: Path | None) -> Path:
        """Return the effective data directory for filesystem persistence."""
        return data_dir if data_dir is not None else _DEFAULT_DATA_DIR

    @staticmethod
    def backend_options(
        *,
        storage_backend: str = "memory",
        data_dir: Path | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """
        Build keyword arguments forwarded to the backend constructor.

        Accepts either a :class:`~palm.app.settings.PalmSettings` instance via
        ``settings=`` or explicit ``storage_backend`` / ``data_dir`` fields.
        """
        settings = overrides.pop("settings", None)
        if settings is not None:
            storage_backend = str(getattr(settings, "storage_backend", storage_backend))
            data_dir = getattr(settings, "data_dir", data_dir)

        backend = storage_backend.strip().lower()
        options: dict[str, Any] = dict(overrides)
        if backend == "filesystem":
            options.setdefault("data_dir", StorageFactory.resolve_data_dir(data_dir))
        return options

    @classmethod
    def select(
        cls,
        engine: StorageEngine,
        name: str,
        *,
        data_dir: Path | None = None,
        settings: Any | None = None,
        **backend_options: Any,
    ) -> BaseBackend:
        """Ensure registration, merge settings, and activate a backend."""
        normalized = name.strip().lower()
        cls.ensure_registered(normalized)
        if settings is not None:
            merged = cls.backend_options(settings=settings, **backend_options)
        else:
            merged = cls.backend_options(
                storage_backend=normalized,
                data_dir=data_dir,
                **backend_options,
            )
        return engine.select(normalized, **merged)

    @classmethod
    def initialize_engine(
        cls,
        engine: StorageEngine,
        *,
        storage_backend: str = "memory",
        data_dir: Path | None = None,
        settings: Any | None = None,
        **backend_options: Any,
    ) -> StorageEngine:
        """Initialize a :class:`~palm.core.storage.StorageEngine` from settings."""
        if settings is not None:
            storage_backend = str(getattr(settings, "storage_backend", storage_backend))
            data_dir = getattr(settings, "data_dir", data_dir)
        backend = storage_backend.strip().lower()
        cls.ensure_registered(backend)
        options = cls.backend_options(
            storage_backend=backend,
            data_dir=data_dir,
            **backend_options,
        )
        engine.initialize(backend=backend, backend_options=options)
        return engine