"""Tests for the storage engine and backends."""

from __future__ import annotations

import pytest

from palm.core import (
    BackendNotOpenError,
    StorageEngine,
    StorageNotConfiguredError,
    storage_registry,
)
from palm.storages import memory, mongodb  # noqa: F401 — register backends
from palm.storages.memory import MemoryBackend
from palm.storages.mongodb import MongoStorageBackend


def test_storage_registry_has_mongodb() -> None:
    assert "mongodb" in storage_registry.names()
    assert storage_registry.get("mongodb") is MongoStorageBackend


def test_memory_backend_lifecycle() -> None:
    backend = MemoryBackend()
    assert not backend.is_open
    backend.open()
    assert backend.is_open
    backend.set("k", "v")
    assert backend.get("k") == "v"
    backend.delete("k")
    assert backend.get("k") is None
    backend.close()
    assert not backend.is_open


def test_memory_backend_requires_open() -> None:
    backend = MemoryBackend()
    with pytest.raises(BackendNotOpenError):
        backend.get("key")


def test_storage_engine_crud_with_memory() -> None:
    engine = StorageEngine()
    engine.initialize(backend="memory")
    engine.set("user", {"id": 1})
    assert engine.get("user") == {"id": 1}
    engine.delete("user")
    assert engine.get("user") is None
    engine.shutdown()
    assert engine.backend is None


def test_storage_engine_requires_backend() -> None:
    engine = StorageEngine()
    engine.initialize()
    with pytest.raises(StorageNotConfiguredError):
        engine.get("missing")


def test_storage_engine_select_switches_backend() -> None:
    engine = StorageEngine()
    engine.initialize()
    engine.select("memory")
    engine.set("x", 1)
    engine.select("mongodb", connection_uri="mongodb://test:27017")
    assert engine.backend_name == "mongodb"
    assert isinstance(engine.backend, MongoStorageBackend)
    assert engine.get("x") is None
    engine.set("x", 2)
    assert engine.get("x") == 2
    engine.shutdown()


def test_mongo_storage_backend_connection_stub() -> None:
    backend = MongoStorageBackend(
        connection_uri="mongodb://mongo:27017",
        database="app",
        collection="kv",
    )
    backend.open()
    assert backend.is_open
    assert backend._client is not None
    assert backend._client["uri"] == "mongodb://mongo:27017"
    backend.set("token", "abc")
    assert backend.get("token") == "abc"
    backend.close()
    assert not backend.is_open
    assert backend._client is None
    with pytest.raises(BackendNotOpenError):
        backend.get("token")


def test_storage_engine_passes_backend_options() -> None:
    engine = StorageEngine()
    engine.initialize()
    backend = engine.select(
        "mongodb",
        connection_uri="mongodb://custom:27017",
        database="custom_db",
    )
    assert backend.connection_uri == "mongodb://custom:27017"
    assert backend.database == "custom_db"
    engine.shutdown()


def test_storage_engine_reselect_same_backend_is_idempotent() -> None:
    engine = StorageEngine()
    engine.initialize(backend="memory")
    first = engine.backend
    second = engine.select("memory")
    assert first is second
    engine.shutdown()