"""Tiered storage is a backend. Its hot map belongs to that instance."""

from __future__ import annotations

import pytest
from drivers.storages.load import open_backend
from drivers.storages.memory.backend import MemoryBackend
from drivers.storages.tiered.backend import TieredBackend

from palm.common.resource.document_storage import get_memory_kv_store, resolve_kv_backend


def test_tiered_writes_through_and_keeps_a_private_hot_map() -> None:
    cold_a = MemoryBackend(name="cold-a")
    cold_b = MemoryBackend(name="cold-b")
    first = TieredBackend(name="tiered", cold=cold_a, hot_max_keys=1)
    second = TieredBackend(name="tiered", cold=cold_b, hot_max_keys=1)
    first.open()
    second.open()
    first.set("a", 1)
    first.set("b", 2)
    assert cold_a.get("a") == 1
    assert cold_a.get("b") == 2
    assert first.get("a") == 1
    assert second.get("a") is None
    assert get_memory_kv_store().get("a") is None
    first.close()
    assert cold_a.get("b") == 2
    assert first.is_open is False
    cold_a.close()
    cold_b.close()


def test_open_backend_builds_a_tiered_instance() -> None:
    cold = MemoryBackend(name="cold")
    cold.open()
    backend = open_backend("tiered", cold=cold, hot_max_keys=2)
    try:
        assert isinstance(backend, TieredBackend)
        backend.set("k", "v")
        assert backend.get("k") == "v"
        assert cold.get("k") == "v"
    finally:
        backend.close()
        cold.close()


def test_kv_rejects_a_tiered_mode() -> None:
    with pytest.raises(ValueError, match="auto, memory, or storage"):
        resolve_kv_backend("tiered", storage=None, storage_backend_name=None)
