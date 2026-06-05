"""
Abstract execution state for behavior trees and context frames.

Engines and nodes depend only on ``BaseState``. Concrete implementations
(dict-backed blackboard, scoped test doubles, etc.) live outside ``palm.core``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseState(ABC):
    """Pluggable key-value state surface shared across ticks and context scopes."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for ``key``, or ``default`` if absent."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key``."""

    @abstractmethod
    def has(self, key: str) -> bool:
        """Return whether ``key`` exists."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove ``key`` if present."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all entries."""

    @abstractmethod
    def snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of all entries."""

    @abstractmethod
    def keys(self) -> list[str]:
        """Return all current keys."""