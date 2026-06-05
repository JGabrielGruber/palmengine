"""
Abstract storage backend contract.

Concrete backends (memory, postgres, mongodb, filesystem) live in
``palm.storages``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseBackend(ABC):
    """Abstract key-value or document persistence surface."""

    def __init__(self, *, name: str) -> None:
        self.name = name

    @abstractmethod
    def open(self) -> None:
        """Open or connect the backend."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Read a value by key."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Write a value by key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a value by key."""

    @abstractmethod
    def close(self) -> None:
        """Close or disconnect the backend."""
