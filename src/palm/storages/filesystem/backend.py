"""
Filesystem storage backend (placeholder).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from palm.core.storage import BaseBackend


class FilesystemBackend(BaseBackend):
    """Stub filesystem persistence backend."""

    def __init__(self, *, name: str = "filesystem", root: Path | None = None) -> None:
        super().__init__(name=name)
        self._root = root or Path("data")

    def open(self) -> None:
        if self._is_open:
            return
        self._root.mkdir(parents=True, exist_ok=True)
        self._is_open = True

    def get(self, key: str) -> Any | None:
        self.ensure_open()
        path = self._root / key
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def set(self, key: str, value: Any) -> None:
        self.ensure_open()
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(value), encoding="utf-8")

    def delete(self, key: str) -> None:
        self.ensure_open()
        path = self._root / key
        if path.exists():
            path.unlink()

    def close(self) -> None:
        self._is_open = False


