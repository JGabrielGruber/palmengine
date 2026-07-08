"""Document and KV storage adapters for local resource providers."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Literal

from palm.core.exceptions import StoragePermissionError
from palm.core.storage import StorageEngine

_DEFAULT_DOCUMENTS_ROOT = Path("data") / "documents"

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
    "FileDocumentStore",
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
    "resolve_documents_root",
    "resolve_kv_backend",
]