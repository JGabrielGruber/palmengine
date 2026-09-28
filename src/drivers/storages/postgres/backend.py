"""
Postgres storage backend — intention stub (docs/STUBS.md ST-002).
"""

from __future__ import annotations

from typing import Any

from palm.core.storage import BaseBackend

_STUB_MSG = (
    "postgres storage is an intention stub (docs/STUBS.md ST-002); "
    "not a durable backend — use memory or filesystem"
)


class PostgresStorageBackend(BaseBackend):
    """Intention stub — refuses all I/O (no silent no-op persistence)."""

    def __init__(self, *, name: str = "postgres") -> None:
        super().__init__(name=name)

    def open(self) -> None:
        raise NotImplementedError(_STUB_MSG)

    def get(self, key: str) -> Any | None:
        raise NotImplementedError(_STUB_MSG)

    def set(self, key: str, value: Any) -> None:
        raise NotImplementedError(_STUB_MSG)

    def delete(self, key: str) -> None:
        raise NotImplementedError(_STUB_MSG)

    def close(self) -> None:
        self._is_open = False
