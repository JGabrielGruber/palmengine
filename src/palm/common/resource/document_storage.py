"""Document and KV storage adapters for local resource providers."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from palm.core.exceptions import StoragePermissionError
from palm.core.storage import StorageEngine

_DEFAULT_DOCUMENTS_ROOT = Path("data") / "documents"
_DEFAULT_KV_COLD_ROOT = Path("data") / "palm" / "kv-cold"
_DEFAULT_TIERED_HOT_MAX_KEYS = 500

KV_STORAGE_PREFIX = "palm:resources:kv"

KvBackendMode = Literal["memory", "storage", "tiered"]


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
    """Resolve ``auto|memory|storage|tiered`` to a concrete KV backend mode."""
    normalized = str(backend or "auto").strip().lower()
    if normalized == "memory":
        return "memory"
    if normalized == "tiered":
        return "tiered"
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
    raise ValueError(
        f"unsupported kv backend {backend!r}; expected auto, memory, storage, or tiered",
    )


def resolve_kv_cold_root(runtime: Any, cold_root: str | Path | None = None) -> Path:
    """Resolve the cold tier root for ``backend: tiered``."""
    if cold_root is not None and str(cold_root).strip():
        return Path(cold_root).expanduser().resolve()
    storage = getattr(runtime, "storage", None)
    backend = storage.backend if storage is not None else None
    data_dir = getattr(backend, "data_dir", None)
    if data_dir is not None:
        return Path(data_dir) / "palm" / "kv-cold"
    settings = getattr(runtime, "settings", None)
    if settings is not None:
        configured = getattr(settings, "data_dir", None)
        if configured is not None:
            return Path(configured) / "palm" / "kv-cold"
    return _DEFAULT_KV_COLD_ROOT.resolve()


def _storage_is_durable(storage_backend_name: str | None) -> bool:
    return storage_backend_name not in (None, "memory")


def resolve_cold_kv_backend(
    *,
    storage: StorageEngine | None,
    storage_backend_name: str | None,
    cold_root: Path,
) -> StorageKvBackend | FileColdKvStore:
    """Pick durable cold storage: StorageEngine when durable, else filesystem spill."""
    if (
        storage is not None
        and storage.backend is not None
        and storage.backend.is_open
        and _storage_is_durable(storage_backend_name)
    ):
        return StorageKvBackend(storage)
    return FileColdKvStore(cold_root)


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


def resolve_documents_root(runtime: Any) -> Path:
    """Best-effort documents root for the ``file`` resource provider."""
    storage = getattr(runtime, "storage", None)
    backend = storage.backend if storage is not None else None
    data_dir = getattr(backend, "data_dir", None)
    if data_dir is not None:
        return Path(data_dir) / "documents"
    settings = getattr(runtime, "settings", None)
    if settings is not None:
        configured = getattr(settings, "data_dir", None)
        if configured is not None:
            return Path(configured) / "documents"
    return _DEFAULT_DOCUMENTS_ROOT


def _validate_relative_document_path(relative_path: str) -> str:
    """Normalize and validate a relative document path."""
    rel = str(relative_path or "").strip().replace("\\", "/")
    if not rel or rel.startswith("/"):
        raise ValueError(f"document path must be a relative path, got {relative_path!r}")
    parts = Path(rel).parts
    if ".." in parts:
        raise ValueError(f"document path must not contain '..': {relative_path!r}")
    return rel


def _validate_glob_pattern(glob_pattern: str) -> str:
    """Reject glob patterns that attempt directory escape."""
    pattern = str(glob_pattern or "**/*").strip().replace("\\", "/")
    if pattern.startswith("/") or ".." in Path(pattern).parts:
        raise ValueError(f"invalid glob pattern {glob_pattern!r}")
    return pattern or "**/*"


def _resolve_document_path(root: Path, relative_path: str) -> Path:
    """Resolve ``relative_path`` under ``root``; reject escapes outside the root."""
    normalized = _validate_relative_document_path(relative_path)
    root_resolved = root.resolve()
    candidate = (root_resolved / normalized).resolve()
    if not candidate.is_relative_to(root_resolved):
        raise ValueError(f"document path {relative_path!r} escapes documents_root")
    return candidate


def _atomic_write_text(path: Path, payload: str) -> int:
    """Write ``payload`` to ``path`` atomically; return bytes written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: str | None = None
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        tmp_path = None
        return len(payload.encode("utf-8"))
    except OSError as exc:
        raise StoragePermissionError(f"Cannot write document file {path}: {exc}") from exc
    finally:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


class FileDocumentStore:
    """Filesystem document store under a single ``documents_root`` directory."""

    def __init__(self, documents_root: Path | str) -> None:
        self._root = Path(documents_root).resolve()
        self._lock = threading.RLock()

    @property
    def documents_root(self) -> Path:
        return self._root

    def read(self, relative_path: str, *, format: str = "json") -> Any:
        with self._lock:
            path = _resolve_document_path(self._root, relative_path)
            try:
                raw = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                return None
            except OSError as exc:
                raise StoragePermissionError(
                    f"Cannot read document {relative_path!r} at {path}: {exc}",
                ) from exc
            if str(format or "json").strip().lower() == "text":
                return raw
            stripped = raw.strip()
            if not stripped:
                return None
            return json.loads(stripped)

    def write(self, relative_path: str, content: Any, *, format: str = "json") -> int:
        with self._lock:
            path = _resolve_document_path(self._root, relative_path)
            if str(format or "json").strip().lower() == "text":
                payload = str(content)
            else:
                payload = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
            return _atomic_write_text(path, payload)

    def delete(self, relative_path: str) -> bool:
        with self._lock:
            path = _resolve_document_path(self._root, relative_path)
            try:
                path.unlink()
                return True
            except FileNotFoundError:
                return False
            except OSError as exc:
                raise StoragePermissionError(
                    f"Cannot delete document {relative_path!r} at {path}: {exc}",
                ) from exc

    def exists(self, relative_path: str) -> bool:
        with self._lock:
            path = _resolve_document_path(self._root, relative_path)
            return path.is_file()

    def list(self, glob_pattern: str = "**/*") -> list[str]:
        with self._lock:
            pattern = _validate_glob_pattern(glob_pattern)
            self._root.mkdir(parents=True, exist_ok=True)
            paths: list[str] = []
            for path in self._root.glob(pattern):
                if path.is_file():
                    paths.append(path.relative_to(self._root).as_posix())
            return sorted(paths)


def _logical_key_to_relative_file(logical_key: str) -> str:
    return f"{_normalize_logical_key(logical_key).replace(':', '/')}.json"


def _relative_file_to_logical_key(relative_path: str) -> str:
    return Path(relative_path).with_suffix("").as_posix().replace("/", ":")


class FileColdKvStore:
    """Filesystem cold tier for ``backend: tiered`` when host storage is in-memory."""

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root).resolve()
        self._lock = threading.RLock()

    @property
    def cold_root(self) -> Path:
        return self._root

    def get(self, namespace: str, logical_key: str) -> Any | None:
        with self._lock:
            path = self._resolve_path(namespace, logical_key)
            try:
                raw = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                return None
            except OSError as exc:
                raise StoragePermissionError(
                    f"Cannot read cold kv key {logical_key!r} at {path}: {exc}",
                ) from exc
            stripped = raw.strip()
            if not stripped:
                return None
            return json.loads(stripped)

    def set(self, namespace: str, logical_key: str, value: Any) -> None:
        with self._lock:
            path = self._resolve_path(namespace, logical_key)
            payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            _atomic_write_text(path, payload)

    def delete(self, namespace: str, logical_key: str) -> bool:
        with self._lock:
            path = self._resolve_path(namespace, logical_key)
            try:
                path.unlink()
                return True
            except FileNotFoundError:
                return False
            except OSError as exc:
                raise StoragePermissionError(
                    f"Cannot delete cold kv key {logical_key!r} at {path}: {exc}",
                ) from exc

    def list_prefix(self, namespace: str, prefix: str = "") -> list[str]:
        with self._lock:
            ns = _normalize_namespace(namespace)
            ns_dir = self._root / ns
            if not ns_dir.exists():
                return []
            normalized_prefix = (
                _normalize_logical_key(prefix) if str(prefix or "").strip() else ""
            )
            keys: list[str] = []
            for path in ns_dir.rglob("*.json"):
                if not path.is_file():
                    continue
                relative = path.relative_to(ns_dir).as_posix()
                logical = _relative_file_to_logical_key(relative)
                if normalized_prefix:
                    if not (
                        logical == normalized_prefix
                        or logical.startswith(f"{normalized_prefix}:")
                    ):
                        continue
                    suffix = logical[len(normalized_prefix) :].lstrip(":")
                    if suffix:
                        keys.append(suffix)
                else:
                    keys.append(logical)
            return sorted(keys)

    def count_keys(self, namespace: str | None = None) -> int:
        with self._lock:
            if namespace is None:
                if not self._root.exists():
                    return 0
                return sum(1 for path in self._root.rglob("*.json") if path.is_file())
            return len(self.list_prefix(namespace))

    def _resolve_path(self, namespace: str, logical_key: str) -> Path:
        ns = _normalize_namespace(namespace)
        relative = _logical_key_to_relative_file(logical_key)
        return _resolve_document_path(self._root / ns, relative)


@dataclass(frozen=True)
class TieredKvConfig:
    """Hot-tier bounds for ``backend: tiered``."""

    hot_max_keys: int = _DEFAULT_TIERED_HOT_MAX_KEYS
    promote_on_read: bool = True


class TieredKvStore:
    """Hot memory cache with write-through cold storage and LRU eviction."""

    def __init__(
        self,
        *,
        hot: MemoryKvStore,
        cold: StorageKvBackend | FileColdKvStore,
        config: TieredKvConfig,
    ) -> None:
        self._hot = hot
        self._cold = cold
        self._config = config
        self._hot_lru: OrderedDict[str, None] = OrderedDict()
        self._lock = threading.RLock()

    @property
    def cold_root(self) -> str:
        cold_root = getattr(self._cold, "cold_root", None)
        if cold_root is not None:
            return str(cold_root)
        return "storage"

    def hot_key_count(self) -> int:
        with self._lock:
            return len(self._hot_lru)

    def cold_key_count(self, namespace: str | None = None) -> int:
        if isinstance(self._cold, FileColdKvStore):
            return self._cold.count_keys(namespace)
        if namespace is None:
            return len(self._cold.list_prefix(KV_STORAGE_PREFIX))
        storage_prefix = build_storage_prefix(namespace, "")
        full_keys = self._cold.list_prefix(storage_prefix)
        return len(logical_keys_from_prefixed(full_keys=full_keys, key_prefix=storage_prefix))

    def get(self, namespace: str, logical_key: str) -> Any | None:
        memory_key = build_memory_key(namespace, logical_key)
        with self._lock:
            value = self._hot.get(memory_key)
            if value is not None:
                self._touch_hot(memory_key)
                return value
        value = self._cold_get(namespace, logical_key)
        if value is None:
            return None
        if self._config.promote_on_read:
            self._promote_hot(namespace, logical_key, value)
        return value

    def set(self, namespace: str, logical_key: str, value: Any) -> None:
        self._cold_set(namespace, logical_key, value)
        self._promote_hot(namespace, logical_key, value)

    def delete(self, namespace: str, logical_key: str) -> bool:
        memory_key = build_memory_key(namespace, logical_key)
        with self._lock:
            hot_deleted = self._hot.delete(memory_key)
            self._hot_lru.pop(memory_key, None)
        cold_deleted = self._cold_delete(namespace, logical_key)
        return hot_deleted or cold_deleted

    def list_prefix(self, namespace: str, prefix: str = "") -> list[str]:
        hot_prefix = build_memory_prefix(namespace, prefix)
        with self._lock:
            hot_keys = set(
                logical_keys_from_prefixed(
                    full_keys=self._hot.list_prefix(hot_prefix),
                    key_prefix=hot_prefix,
                ),
            )
        cold_keys = set(self._cold_list_prefix(namespace, prefix))
        return sorted(hot_keys | cold_keys)

    def _cold_get(self, namespace: str, logical_key: str) -> Any | None:
        if isinstance(self._cold, FileColdKvStore):
            return self._cold.get(namespace, logical_key)
        return self._cold.get(build_storage_key(namespace, logical_key))

    def _cold_set(self, namespace: str, logical_key: str, value: Any) -> None:
        if isinstance(self._cold, FileColdKvStore):
            self._cold.set(namespace, logical_key, value)
            return
        self._cold.set(build_storage_key(namespace, logical_key), value)

    def _cold_delete(self, namespace: str, logical_key: str) -> bool:
        if isinstance(self._cold, FileColdKvStore):
            return self._cold.delete(namespace, logical_key)
        return self._cold.delete(build_storage_key(namespace, logical_key))

    def _cold_list_prefix(self, namespace: str, prefix: str) -> list[str]:
        if isinstance(self._cold, FileColdKvStore):
            return self._cold.list_prefix(namespace, prefix)
        storage_prefix = build_storage_prefix(namespace, prefix)
        full_keys = self._cold.list_prefix(storage_prefix)
        return logical_keys_from_prefixed(full_keys=full_keys, key_prefix=storage_prefix)

    def _promote_hot(self, namespace: str, logical_key: str, value: Any) -> None:
        memory_key = build_memory_key(namespace, logical_key)
        with self._lock:
            self._hot.set(memory_key, value)
            self._touch_hot(memory_key)
            self._evict_hot_if_needed()

    def _touch_hot(self, memory_key: str) -> None:
        self._hot_lru.pop(memory_key, None)
        self._hot_lru[memory_key] = None

    def _evict_hot_if_needed(self) -> None:
        while len(self._hot_lru) > self._config.hot_max_keys:
            evicted_key, _ = self._hot_lru.popitem(last=False)
            self._hot.delete(evicted_key)


_TIERED_STORES: dict[str, TieredKvStore] = {}
_TIERED_STORES_LOCK = threading.RLock()


def get_tiered_kv_store(
    *,
    storage: StorageEngine | None,
    storage_backend_name: str | None,
    cold_root: Path,
    config: TieredKvConfig,
) -> TieredKvStore:
    """Return a process-wide tiered store for a cold-root and hot-limit pair."""
    cache_key = f"{cold_root}:{storage_backend_name}:{config.hot_max_keys}"
    with _TIERED_STORES_LOCK:
        existing = _TIERED_STORES.get(cache_key)
        if existing is not None:
            return existing
        cold = resolve_cold_kv_backend(
            storage=storage,
            storage_backend_name=storage_backend_name,
            cold_root=cold_root,
        )
        store = TieredKvStore(hot=get_memory_kv_store(), cold=cold, config=config)
        _TIERED_STORES[cache_key] = store
        return store


def clear_tiered_kv_stores() -> None:
    """Reset tiered store singletons (tests)."""
    with _TIERED_STORES_LOCK:
        _TIERED_STORES.clear()


def build_tiered_preflight_stats(
    runtime: Any,
    storage: StorageEngine | None,
    *,
    namespace: str = "default",
    hot_max_keys: int = _DEFAULT_TIERED_HOT_MAX_KEYS,
) -> dict[str, Any]:
    """Summarize hot/cold tier usage for doctor reports."""
    cold_root = resolve_kv_cold_root(runtime)
    storage_backend_name = storage.backend_name if storage is not None else None
    store = get_tiered_kv_store(
        storage=storage,
        storage_backend_name=storage_backend_name,
        cold_root=cold_root,
        config=TieredKvConfig(hot_max_keys=hot_max_keys),
    )
    return {
        "cold_root": store.cold_root,
        "hot_keys": store.hot_key_count(),
        "cold_keys": store.cold_key_count(namespace),
        "hot_max_keys": hot_max_keys,
    }


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
    "FileColdKvStore",
    "FileDocumentStore",
    "KV_STORAGE_PREFIX",
    "MemoryKvStore",
    "StorageKvBackend",
    "TieredKvConfig",
    "TieredKvStore",
    "build_memory_key",
    "build_memory_prefix",
    "build_storage_key",
    "build_storage_prefix",
    "build_tiered_preflight_stats",
    "clear_memory_kv_store",
    "clear_tiered_kv_stores",
    "get_memory_kv_store",
    "get_tiered_kv_store",
    "list_storage_keys_with_prefix",
    "logical_keys_from_prefixed",
    "resolve_cold_kv_backend",
    "resolve_documents_root",
    "resolve_kv_backend",
    "resolve_kv_cold_root",
]