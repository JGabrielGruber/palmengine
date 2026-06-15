"""
Filesystem storage backend — production-grade JSON persistence on local disk.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from palm.core.exceptions import ConfigurationError, StoragePermissionError
from palm.core.storage import BaseBackend

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path("data")
_JSON_SUFFIX = ".json"


def _resolve_data_dir(data_dir: Path | str | None, *, root: Path | str | None) -> Path:
    """Resolve and validate the storage root directory."""
    candidate = data_dir if data_dir is not None else root
    resolved = Path(candidate) if candidate is not None else _DEFAULT_DATA_DIR
    if resolved.exists() and not resolved.is_dir():
        raise ConfigurationError(f"Filesystem storage data_dir must be a directory: {resolved}")
    return resolved


def _validate_key_segment(segment: str) -> None:
    """Reject path traversal and separator characters in a key segment."""
    if segment in (".", ".."):
        raise ConfigurationError(f"Storage key segment must not be {segment!r}")
    if "/" in segment or "\\" in segment:
        raise ConfigurationError(
            f"Storage key segment must not contain path separators: {segment!r}",
        )


def _key_to_relpath(key: str) -> Path:
    """Map colon-separated storage keys to nested JSON file paths."""
    parts = [segment for segment in key.split(":") if segment]
    if not parts:
        raise ConfigurationError("Storage key must not be empty")
    for segment in parts:
        _validate_key_segment(segment)
    return Path(*parts).with_suffix(_JSON_SUFFIX)


def _resolve_under_root(root: Path, relative: Path) -> Path:
    """Resolve ``relative`` under ``root``; reject escapes outside the root."""
    root_resolved = root.resolve()
    candidate = (root_resolved / relative).resolve()
    if not candidate.is_relative_to(root_resolved):
        raise StoragePermissionError(
            f"Storage path {relative!s} escapes data directory {root_resolved}",
        )
    return candidate


class FilesystemStorageBackend(BaseBackend):
    """
    Durable JSON key-value storage with atomic writes and namespace paths.

    Keys such as ``palm:instances:inst-abc`` map to
    ``<data_dir>/palm/instances/inst-abc.json``. Legacy v0.6 flat files
    (``<data_dir>/palm:instances:inst-abc``) are read for backward compatibility;
    new writes always use the nested layout.
    """

    def __init__(
        self,
        *,
        name: str = "filesystem",
        data_dir: Path | str | None = None,
        root: Path | str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._data_dir = _resolve_data_dir(data_dir, root=root)
        self._lock = threading.RLock()

    @property
    def data_dir(self) -> Path:
        """Root directory for persisted JSON files."""
        return self._data_dir

    def open(self) -> None:
        if self._is_open:
            return
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StoragePermissionError(
                f"Cannot create filesystem storage directory {self._data_dir}: {exc}"
            ) from exc
        self._is_open = True

    def get(self, key: str) -> Any | None:
        self.ensure_open()
        with self._lock:
            path = self._resolve_read_path(key)
            if path is None:
                return None
            try:
                raw = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                return None
            except OSError as exc:
                raise StoragePermissionError(
                    f"Cannot read storage key {key!r} at {path}: {exc}"
                ) from exc
            return self._decode_payload(key, raw, path=path)

    def set(self, key: str, value: Any) -> None:
        self.ensure_open()
        with self._lock:
            path = self._resolve_data_path(key)
            payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            self._atomic_write(path, payload)

    def delete(self, key: str) -> None:
        self.ensure_open()
        with self._lock:
            removed = False
            for path in self._candidate_paths(key):
                try:
                    path.unlink()
                    removed = True
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    raise StoragePermissionError(
                        f"Cannot delete storage key {key!r} at {path}: {exc}"
                    ) from exc
            if not removed:
                return

    def close(self) -> None:
        self._is_open = False

    def _resolve_read_path(self, key: str) -> Path | None:
        for path in self._candidate_paths(key):
            if path.exists():
                return path
        return None

    def _candidate_paths(self, key: str) -> tuple[Path, ...]:
        modern = self._resolve_data_path(key)
        legacy = self._resolve_legacy_path(key)
        return (modern, legacy)

    def _resolve_data_path(self, key: str) -> Path:
        return _resolve_under_root(self._data_dir, _key_to_relpath(key))

    def _resolve_legacy_path(self, key: str) -> Path:
        if ".." in key or "/" in key or "\\" in key:
            raise ConfigurationError(
                f"Storage key must not contain path traversal or separators: {key!r}",
            )
        return _resolve_under_root(self._data_dir, Path(key))

    def _decode_payload(self, key: str, raw: str, *, path: Path) -> Any | None:
        stripped = raw.strip()
        if not stripped:
            logger.warning("Empty storage payload for key %r at %s", key, path)
            return None
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            logger.warning(
                "Corrupted JSON for storage key %r at %s; treating as missing",
                key,
                path,
            )
            return None

    def _atomic_write(self, path: Path, payload: str) -> None:
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
        except OSError as exc:
            raise StoragePermissionError(f"Cannot write storage file {path}: {exc}") from exc
        finally:
            if tmp_path is not None:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass


# Backward-compatible alias (v0.6 registered name).
FilesystemBackend = FilesystemStorageBackend
