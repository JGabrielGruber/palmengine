"""Tests for document/KV storage adapters."""

from __future__ import annotations

import pytest

from palm.common.resource.document_storage import (
    MemoryKvStore,
    StorageKvBackend,
    build_memory_key,
    build_storage_key,
    clear_memory_kv_store,
    get_memory_kv_store,
    logical_keys_from_prefixed,
    resolve_kv_backend,
)
from palm.core.storage import StorageEngine


def setup_function() -> None:
    clear_memory_kv_store()


def test_memory_kv_store_round_trip() -> None:
    store = MemoryKvStore()
    store.set("ns:key", {"visit_count": 1})
    assert store.get("ns:key") == {"visit_count": 1}
    assert store.delete("ns:key") is True
    assert store.get("ns:key") is None
    assert store.delete("ns:missing") is False


def test_memory_kv_store_list_prefix() -> None:
    store = MemoryKvStore()
    store.set(build_memory_key("coconut", "players/alice"), {"a": 1})
    store.set(build_memory_key("coconut", "players/bob"), {"b": 2})
    store.set(build_memory_key("coconut", "rumors/1"), {"r": 1})
    keys = store.list_prefix(build_memory_key("coconut", "players"))
    assert keys == [
        build_memory_key("coconut", "players/alice"),
        build_memory_key("coconut", "players/bob"),
    ]


def test_build_storage_key() -> None:
    assert build_storage_key("coconut", "players/alice") == (
        "palm:resources:kv:coconut:players:alice"
    )


def test_resolve_kv_backend_auto_memory() -> None:
    storage = StorageEngine()
    storage.initialize()
    storage.select("memory")
    assert (
        resolve_kv_backend("auto", storage=storage, storage_backend_name="memory") == "memory"
    )
    storage.shutdown()


def test_resolve_kv_backend_auto_filesystem(tmp_path) -> None:
    storage = StorageEngine()
    storage.initialize()
    storage.select("filesystem", data_dir=tmp_path)
    assert (
        resolve_kv_backend("auto", storage=storage, storage_backend_name="filesystem")
        == "storage"
    )
    storage.shutdown()


def test_resolve_kv_backend_storage_requires_open_storage() -> None:
    storage = StorageEngine()
    storage.initialize()
    with pytest.raises(ValueError, match="open StorageEngine"):
        resolve_kv_backend("storage", storage=storage, storage_backend_name=None)
    storage.shutdown()


def test_storage_kv_backend_round_trip(tmp_path) -> None:
    storage = StorageEngine()
    storage.initialize()
    storage.select("filesystem", data_dir=tmp_path)
    backend = StorageKvBackend(storage)
    key = build_storage_key("coconut", "players/alice")
    backend.set(key, {"visit_count": 2})
    assert backend.get(key) == {"visit_count": 2}
    assert backend.delete(key) is True
    assert backend.get(key) is None
    storage.shutdown()


def test_storage_kv_backend_list_prefix(tmp_path) -> None:
    storage = StorageEngine()
    storage.initialize()
    storage.select("filesystem", data_dir=tmp_path)
    backend = StorageKvBackend(storage)
    backend.set(build_storage_key("coconut", "players/alice"), {"a": 1})
    backend.set(build_storage_key("coconut", "players/bob"), {"b": 2})
    keys = backend.list_prefix(build_storage_key("coconut", "players"))
    logical = logical_keys_from_prefixed(
        full_keys=keys,
        key_prefix=build_storage_key("coconut", "players"),
    )
    assert logical == ["alice", "bob"]
    storage.shutdown()


def test_get_memory_kv_store_is_process_singleton() -> None:
    get_memory_kv_store().set(build_memory_key("demo", "x"), 1)
    assert get_memory_kv_store().get(build_memory_key("demo", "x")) == 1