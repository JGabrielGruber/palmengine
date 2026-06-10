"""Filesystem storage app — production JSON persistence backend."""

from palm.storages.filesystem import registry as registry
from palm.storages.filesystem.backend import FilesystemBackend, FilesystemStorageBackend

__all__ = ["FilesystemBackend", "FilesystemStorageBackend", "registry"]
