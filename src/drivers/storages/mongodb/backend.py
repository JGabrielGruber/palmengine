"""
MongoDB storage backend — intention stub (docs/STUBS.md ST-002).
"""

from __future__ import annotations

from typing import Any

from palm.core.storage import BaseBackend

_STUB_MSG = (
    "mongodb storage is an intention stub (docs/STUBS.md ST-002); "
    "not a durable backend — use memory or filesystem"
)


class MongoStorageBackend(BaseBackend):
    """Intention stub — refuses all I/O (no silent in-memory fake Mongo)."""

    def __init__(
        self,
        *,
        name: str = "mongodb",
        connection_uri: str = "mongodb://localhost:27017",
        database: str = "palm",
        collection: str = "storage",
    ) -> None:
        super().__init__(name=name)
        self._connection_uri = connection_uri
        self._database = database
        self._collection = collection

    @property
    def connection_uri(self) -> str:
        return self._connection_uri

    @property
    def database(self) -> str:
        return self._database

    @property
    def collection(self) -> str:
        return self._collection

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
