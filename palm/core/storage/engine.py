"""
Storage engine — coordinates persistence backends.

Resolves backends by name from ``storage_registry``. Core stays free of
concrete database or filesystem drivers.
"""

from __future__ import annotations

from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.registry import storage_registry
from palm.core.storage.base_backend import BaseBackend


class StorageEngine(BasePalmEngine):
    """Manages lifecycle and lookup of registered storage backends."""

    def __init__(self) -> None:
        super().__init__(name="storage")
        self._active: BaseBackend | None = None
        self._backend_name: str | None = None

    @property
    def backend(self) -> BaseBackend | None:
        return self._active

    def select(self, name: str) -> BaseBackend:
        """Activate the storage backend registered under ``name``."""
        if self._backend_name != name or self._active is None:
            if self._active is not None:
                self._active.close()
            cls = storage_registry.get(name)
            backend = cls(name=name)
            backend.open()
            self._active = backend
            self._backend_name = name
        return self._active

    def _do_initialize(self, **options: Any) -> None:
        default = options.get("backend")
        if isinstance(default, str):
            self.select(default)

    def _do_shutdown(self) -> None:
        if self._active is not None:
            self._active.close()
        self._active = None
        self._backend_name = None
