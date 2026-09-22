"""Filesystem storage registration."""

from palm.core.registry import storage_registry
from plugins.storages.filesystem.backend import FilesystemStorageBackend

storage_registry.register("filesystem", FilesystemStorageBackend)
