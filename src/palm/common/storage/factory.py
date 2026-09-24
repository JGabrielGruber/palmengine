"""
StorageFactory — select a storage backend the application already registered.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from palm.core.exceptions import RegistryError
from palm.core.registry import storage_registry
from palm.core.storage import BaseBackend, StorageEngine

_DEFAULT_DATA_DIR = Path("data")


class StorageFactory:
    """Select a registered storage backend and apply settings options.

    The application imports the storage plugin. This factory does not.
    """

    @staticmethod
    def ensure_registered(name: str) -> None:
        """Fail closed when *name* is not already in the storage registry."""
        normalized = name.strip().lower()
        if normalized in storage_registry.names():
            return
        raise RegistryError(
            f"Storage backend {name!r} is not registered. "
            "The application installs that storage plugin before storage select."
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
        storage_backend: str,
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
