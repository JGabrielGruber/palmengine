"""
Postgres storage backend (placeholder).
"""

from __future__ import annotations

from typing import Any

from palm.core.storage import BaseBackend


class PostgresStorageBackend(BaseBackend):
    """Stub Postgres persistence backend."""

    def __init__(self, *, name: str = "postgres") -> None:
        super().__init__(name=name)

    def open(self) -> None:
        if self._is_open:
            return
        self._is_open = True

    def get(self, key: str) -> Any | None:
        self.ensure_open()
        return None

    def set(self, key: str, value: Any) -> None:
        self.ensure_open()

    def delete(self, key: str) -> None:
        self.ensure_open()

    def close(self) -> None:
        self._is_open = False


