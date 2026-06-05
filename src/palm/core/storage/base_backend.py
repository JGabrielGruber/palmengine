"""
Abstract storage backend contract.

Concrete backends (memory, postgres, mongodb, filesystem) live in
``palm.storages``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from palm.core.exceptions import BackendNotOpenError


class BaseBackend(ABC):
    """Abstract key-value or document persistence surface."""

    def __init__(self, *, name: str) -> None:
        self.name = name
        self._is_open = False

    @property
    def is_open(self) -> bool:
        """Whether the backend has been opened and not yet closed."""
        return self._is_open

    def ensure_open(self) -> None:
        """Raise if the backend is not open."""
        if not self._is_open:
            raise BackendNotOpenError(
                f"Storage backend {self.name!r} is not open. Call open() first."
            )

    @abstractmethod
    def open(self) -> None:
        """Open or connect the backend. Idempotent when already open."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Read a value by key. Returns ``None`` when the key is absent."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Write a value by key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a value by key. No-op when the key is absent."""

    @abstractmethod
    def close(self) -> None:
        """Close or disconnect the backend. Idempotent when already closed."""