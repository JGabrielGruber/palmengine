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
        if self._is_open:
            return
        self._is_open = True

    def get(self, key: str) -> Any | None:
        self.ensure_open()
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        self.ensure_open()
        self._data[key] = value

    def delete(self, key: str) -> None:
        self.ensure_open()
        self._data.pop(key, None)

    def close(self) -> None:
        if not self._is_open:
            return
        self._data.clear()
        self._is_open = False


storage_registry.register("memory", MemoryBackend)