"""Document and KV storage adapters for local resource providers."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Literal

from palm.core.storage import StorageEngine

KV_STORAGE_PREFIX = "palm:resources:kv"

KvBackendMode = Literal["memory", "storage"]


def build_storage_key(namespace: str, logical_key: str) -> str:
    """Map a logical KV key to a StorageEngine key."""
    ns = _normalize_namespace(namespace)
    key = _normalize_logical_key(logical_key)
    return f"{KV_STORAGE_PREFIX}:{ns}:{key}"


def build_memory_key(namespace: str, logical_key: str) -> str:
    """Map a logical KV key to an in-process memory store key."""
    ns = _normalize_namespace(namespace)
    key = _normalize_logical_key(logical_key)
    return f"{ns}:{key}"


def build_storage_prefix(namespace: str, prefix: str = "") -> str:
    ns = _normalize_namespace(namespace)
    trimmed = _normalize_logical_key(prefix) if str(prefix or "").strip() else ""
    if trimmed:
        return f"{KV_STORAGE_PREFIX}:{ns}:{trimmed}"
    return f"{KV_STORAGE_PREFIX}:{ns}"


def build_memory_prefix(namespace: str, prefix: str = "") -> str:
    ns = _normalize_namespace(namespace)
    trimmed = _normalize_logical_key(prefix) if str(prefix or "").strip() else ""
    if trimmed:
        return f"{ns}:{trimmed}"
    return ns


def resolve_kv_backend(
    backend: str | None,
    *,
    storage: StorageEngine | None,
    storage_backend_name: str | None,
) -> KvBackendMode:
    """Resolve ``auto|memory|storage`` to a concrete KV backend mode."""
    normalized = str(backend or "auto").strip().lower()
    if normalized == "memory":
        return "memory"
    if normalized == "storage":
        if storage is None or storage.backend is None or not storage.backend.is_open:
            raise ValueError("kv backend=storage requires an open StorageEngine")
        return "storage"
    if normalized == "auto":
        if storage_backend_name == "filesystem":
            if storage is None or storage.backend is None or not storage.backend.is_open:
                return "memory"
            return "storage"
        if storage is not None and storage.backend is not None and storage.backend.is_open:
            if storage_backend_name not in (None, "memory"):
                return "storage"
        return "memory"
    raise ValueError(f"unsupported kv backend {backend!r}; expected auto, memory, or storage")


class MemoryKvStore:
    """Thread-safe in-process key-value store for kv provider ``memory`` backend."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._data.pop(key, None) is not None

    def list_prefix(self, prefix: str) -> list[str]:
        with self._lock:
            return sorted(key for key in self._data if key.startswith(prefix))

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


_MEMORY_STORE = MemoryKvStore()


def get_memory_kv_store() -> MemoryKvStore:
    """Return the process-wide in-memory KV store."""
    return _MEMORY_STORE


def clear_memory_kv_store() -> None:
    """Clear the process-wide in-memory KV store (tests)."""
    _MEMORY_STORE.clear()


class StorageKvBackend:
    """KV adapter over the host StorageEngine."""

    def __init__(self, storage: StorageEngine) -> None:
        self._storage = storage

    def get(self, storage_key: str) -> Any | None:
        return self._storage.get(storage_key)

    def set(self, storage_key: str, value: Any) -> None:
        self._storage.set(storage_key, value)

    def delete(self, storage_key: str) -> bool:
        existing = self._storage.get(storage_key)
        if existing is None:
            return False
        self._storage.delete(storage_key)
        return True

    def list_prefix(self, storage_prefix: str) -> list[str]:
        return list_storage_keys_with_prefix(self._storage, storage_prefix)


def list_storage_keys_with_prefix(storage: StorageEngine, prefix: str) -> list[str]:
    """List StorageEngine keys that start with ``prefix``."""
    backend = storage.backend
    if backend is None or not backend.is_open:
        return []

    from palm.storages.filesystem.backend import FilesystemStorageBackend
    from palm.storages.memory.backend import MemoryBackend

    if isinstance(backend, MemoryBackend):
        return sorted(key for key in backend._data if key.startswith(prefix))

    if isinstance(backend, FilesystemStorageBackend):
        return _list_filesystem_storage_prefix(backend.data_dir, prefix)

    return []


def logical_keys_from_prefixed(
    *,
    full_keys: list[str],
    key_prefix: str,
    strip_chars: str = ":",
) -> list[str]:
    """Strip a namespace prefix and return logical key suffixes."""
    if not full_keys:
        return []
    base = key_prefix.rstrip(strip_chars)
    logical: list[str] = []
    for key in full_keys:
        if not key.startswith(base):
            continue
        suffix = key[len(base) :].lstrip(strip_chars).lstrip("/")
        if suffix:
            logical.append(suffix)
    return sorted(logical)


def _normalize_namespace(namespace: str | None) -> str:
    ns = str(namespace or "default").strip()
    if not ns:
        return "default"
    if ":" in ns or "/" in ns or "\\" in ns:
        raise ValueError(f"invalid kv namespace {namespace!r}")
    return ns


def _normalize_logical_key(logical_key: str) -> str:
    """Normalize author-facing keys to colon segments for storage backends."""
    key = str(logical_key or "").strip()
    if not key:
        raise ValueError("logical key must be non-empty")
    if ".." in key:
        raise ValueError(f"invalid logical key {logical_key!r}")
    return key.replace("\\", "/").replace("/", ":")


def _list_filesystem_storage_prefix(data_dir: Path, prefix: str) -> list[str]:
    rel_dir = Path(*[segment for segment in prefix.split(":") if segment])
    root = data_dir / rel_dir
    if not root.exists():
        return []
    keys: list[str] = []
    for path in root.rglob("*.json"):
        if not path.is_file():
            continue
        relative = path.relative_to(data_dir).with_suffix("")
        keys.append(":".join(relative.parts))
    return sorted(keys)


__all__ = [
    "KV_STORAGE_PREFIX",
    "MemoryKvStore",
    "StorageKvBackend",
    "build_memory_key",
    "build_memory_prefix",
    "build_storage_key",
    "build_storage_prefix",
    "clear_memory_kv_store",
    "get_memory_kv_store",
    "list_storage_keys_with_prefix",
    "logical_keys_from_prefixed",
    "resolve_kv_backend",
]