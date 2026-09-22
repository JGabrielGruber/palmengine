"""Filesystem storage app — production JSON persistence backend."""

from plugins.storages.filesystem import registry as registry
from plugins.storages.filesystem.backend import FilesystemBackend, FilesystemStorageBackend

__all__ = ["FilesystemBackend", "FilesystemStorageBackend", "registry"]
