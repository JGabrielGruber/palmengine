"""Memory storage app — Dict-backed ephemeral storage."""

from palm.storages.memory import registry as registry
from palm.storages.memory.backend import MemoryBackend

__all__ = ["MemoryBackend", "registry"]
