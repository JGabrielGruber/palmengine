"""Filesystem storage registration."""

from palm.core.registry import storage_registry
from palm.storages.filesystem.backend import FilesystemBackend

storage_registry.register("filesystem", FilesystemBackend)
