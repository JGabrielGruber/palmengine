"""Filesystem storage app — Stub filesystem persistence backend."""

from palm.storages.filesystem import registry as registry
from palm.storages.filesystem.backend import FilesystemBackend

__all__ = ["FilesystemBackend", "registry"]
