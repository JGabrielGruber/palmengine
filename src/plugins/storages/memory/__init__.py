"""Memory storage app — Dict-backed ephemeral storage."""

from plugins.storages.memory import registry as registry
from plugins.storages.memory.backend import MemoryBackend

__all__ = ["MemoryBackend", "registry"]
