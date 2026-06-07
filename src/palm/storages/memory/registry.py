"""Memory storage registration."""

from palm.core.registry import storage_registry
from palm.storages.memory.backend import MemoryBackend

storage_registry.register("memory", MemoryBackend)
