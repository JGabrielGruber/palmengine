"""
In-memory storage backend — development and testing default.
"""

from __future__ import annotations

from typing import Any

from palm.core.registry import storage_registry
from palm.core.storage import BaseBackend


class MemoryBackend(BaseBackend):
    """Dict-backed ephemeral storage."""

    def __init__(self, *, name: str = "memory") -> None:
        super().__init__(name=name)
        self._data: dict[str, Any] = {}

    def open(self) -> None:
        pass

    def get(self, key: str) -> Any | None:
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def close(self) -> None:
        self._data.clear()


storage_registry.register("memory", MemoryBackend)
