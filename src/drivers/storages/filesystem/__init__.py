"""Filesystem storage app — production JSON persistence backend."""

from drivers.storages.filesystem import registry as registry
from drivers.storages.filesystem.backend import FilesystemBackend, FilesystemStorageBackend

__all__ = ["FilesystemBackend", "FilesystemStorageBackend", "registry"]
