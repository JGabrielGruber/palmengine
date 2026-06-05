"""
Storage engine — coordinates persistence backends.

Resolves backends by name from ``storage_registry``. Core stays free of
concrete database or filesystem drivers.
"""

from __future__ import annotations

from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.exceptions import StorageNotConfiguredError
from palm.core.registry import storage_registry
from palm.core.storage.base_backend import BaseBackend


class StorageEngine(BasePalmEngine):
    """
    Manages lifecycle and CRUD operations for a single active storage backend.

    Use ``select`` to activate a registered backend, then ``get`` / ``set`` /
    ``delete`` through the engine. All operations require an initialized,
    open backend.
    """

    def __init__(self) -> None:
        super().__init__(name="storage")
        self._active: BaseBackend | None = None
        self._backend_name: str | None = None

    @property
    def backend(self) -> BaseBackend | None:
        """The currently active backend, if any."""
        return self._active

    @property
    def backend_name(self) -> str | None:
        """Registered name of the active backend."""
        return self._backend_name

    def select(self, name: str, **backend_options: Any) -> BaseBackend:
        """
        Activate the storage backend registered under ``name``.

        Closes any previously active backend. ``backend_options`` are forwarded
        to the backend constructor (e.g. Mongo connection settings).
        """
        if self._backend_name == name and self._active is not None and self._active.is_open:
            return self._active

        self._close_active()
        cls = storage_registry.get(name)
        backend = cls(name=name, **backend_options)
        backend.open()
        self._active = backend
        self._backend_name = name
        return self._active

    def get(self, key: str) -> Any | None:
        """Read ``key`` from the active backend."""
        return self._require_backend().get(key)

    def set(self, key: str, value: Any) -> None:
        """Write ``value`` under ``key`` on the active backend."""
        self._require_backend().set(key, value)

    def delete(self, key: str) -> None:
        """Remove ``key`` from the active backend."""
        self._require_backend().delete(key)

    def _require_backend(self) -> BaseBackend:
        if self._active is None or not self._active.is_open:
            raise StorageNotConfiguredError(
                "No storage backend is active. Call select() after initialize()."
            )
        return self._active

    def _close_active(self) -> None:
        if self._active is not None:
            self._active.close()
        self._active = None
        self._backend_name = None

    def _do_initialize(self, **options: Any) -> None:
        default = options.get("backend")
        if isinstance(default, str):
            backend_options = options.get("backend_options")
            opts = backend_options if isinstance(backend_options, dict) else {}
            self.select(default, **opts)

    def _do_shutdown(self) -> None:
        self._close_active()