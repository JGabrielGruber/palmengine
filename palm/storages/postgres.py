"""
Postgres storage backend (placeholder).
"""

from __future__ import annotations

from typing import Any

from palm.core.registry import storage_registry
from palm.core.storage import BaseBackend


class PostgresStorageBackend(BaseBackend):
    """Stub Postgres persistence backend."""

    def open(self) -> None:
        pass

    def get(self, key: str) -> Any | None:
        return None

    def set(self, key: str, value: Any) -> None:
        pass

    def delete(self, key: str) -> None:
        pass

    def close(self) -> None:
        pass


storage_registry.register("postgres", PostgresStorageBackend)
