"""Tests for document/KV storage adapters."""

from __future__ import annotations

import pytest

from palm.common.resource.document_storage import (
    FileColdKvStore,
    FileDocumentStore,
    MemoryKvStore,
    StorageKvBackend,
    TieredKvConfig,
    TieredKvStore,
    build_memory_key,
    build_storage_key,
    clear_memory_kv_store,
    clear_tiered_kv_stores,
    get_memory_kv_store,
    logical_keys_from_prefixed,
    resolve_kv_backend,
)
from palm.core.storage import StorageEngine


def setup_function() -> None:
    clear_memory_kv_store()
    clear_tiered_kv_stores()


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


def test_resolve_kv_backend_tiered() -> None:
    storage = StorageEngine()
    storage.initialize()
    assert resolve_kv_backend("tiered", storage=storage, storage_backend_name="memory") == "tiered"
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


def test_file_document_store_json_round_trip(tmp_path) -> None:
    store = FileDocumentStore(tmp_path / "documents")
    nbytes = store.write("profiles/alice.json", {"visit_count": 2})
    assert nbytes > 0
    assert store.read("profiles/alice.json") == {"visit_count": 2}
    assert store.exists("profiles/alice.json") is True
    assert store.delete("profiles/alice.json") is True
    assert store.exists("profiles/alice.json") is False


def test_file_document_store_blocks_traversal(tmp_path) -> None:
    store = FileDocumentStore(tmp_path / "documents")
    with pytest.raises(ValueError, match="\\.\\."):
        store.read("../secret.json")
    with pytest.raises(ValueError, match="\\.\\."):
        store.read("profiles/../../secret.json")


def test_tiered_kv_store_write_through_and_promote(tmp_path) -> None:
    hot = MemoryKvStore()
    cold = FileColdKvStore(tmp_path / "kv-cold")
    store = TieredKvStore(hot=hot, cold=cold, config=TieredKvConfig(hot_max_keys=2))
    store.set("coconut", "players/alice", {"visit_count": 1})
    assert cold.get("coconut", "players/alice") == {"visit_count": 1}
    hot.delete(build_memory_key("coconut", "players/alice"))
    assert store.get("coconut", "players/alice") == {"visit_count": 1}
    assert hot.get(build_memory_key("coconut", "players/alice")) == {"visit_count": 1}


def test_tiered_kv_store_evicts_lru_from_hot(tmp_path) -> None:
    hot = MemoryKvStore()
    cold = FileColdKvStore(tmp_path / "kv-cold")
    store = TieredKvStore(hot=hot, cold=cold, config=TieredKvConfig(hot_max_keys=2))
    store.set("coconut", "players/alice", {"n": 1})
    store.set("coconut", "players/bob", {"n": 2})
    store.set("coconut", "players/charlie", {"n": 3})
    assert hot.get(build_memory_key("coconut", "players/alice")) is None
    assert store.get("coconut", "players/alice") == {"n": 1}
    assert store.list_prefix("coconut", "players") == ["alice", "bob", "charlie"]
    assert cold.count_keys("coconut") == 3


def test_file_document_store_list_glob(tmp_path) -> None:
    store = FileDocumentStore(tmp_path / "documents")
    store.write("coconut/players/alice.json", {"a": 1})
    store.write("coconut/players/bob.json", {"b": 2})
    store.write("notes/readme.txt", "hello", format="text")
    paths = store.list("coconut/**/*.json")
    assert paths == ["coconut/players/alice.json", "coconut/players/bob.json"]