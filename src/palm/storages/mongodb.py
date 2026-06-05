"""
MongoDB storage backend — connection stub with in-memory fallback.

Uses a placeholder client until the official driver is wired. Connection
settings are accepted now so callers can configure real deployments later.
"""

from __future__ import annotations

from typing import Any

from palm.core.registry import storage_registry
from palm.core.storage import BaseBackend


class MongoStorageBackend(BaseBackend):
    """
    MongoDB persistence backend (stub).

    ``open`` simulates a connection handshake and stores documents in an
    in-process dict. Replace ``_client`` wiring with ``pymongo.MongoClient``
    when the driver dependency is added.
    """

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
        self._client: dict[str, str] | None = None
        self._documents: dict[str, Any] = {}

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
        if self._is_open:
            return
        # Placeholder: represent a connected client without pymongo
        self._client = {
            "uri": self._connection_uri,
            "database": self._database,
            "collection": self._collection,
        }
        self._is_open = True

    def get(self, key: str) -> Any | None:
        self.ensure_open()
        return self._documents.get(key)

    def set(self, key: str, value: Any) -> None:
        self.ensure_open()
        self._documents[key] = value

    def delete(self, key: str) -> None:
        self.ensure_open()
        self._documents.pop(key, None)

    def close(self) -> None:
        if not self._is_open:
            return
        self._client = None
        self._documents.clear()
        self._is_open = False


storage_registry.register("mongodb", MongoStorageBackend)