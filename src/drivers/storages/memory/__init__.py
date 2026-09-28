"""Memory storage app — Dict-backed ephemeral storage."""

from drivers.storages.memory import registry as registry
from drivers.storages.memory.backend import MemoryBackend

__all__ = ["MemoryBackend", "registry"]
