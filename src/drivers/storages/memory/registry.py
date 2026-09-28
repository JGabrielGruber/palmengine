"""Memory storage registration."""

from palm.core.registry import storage_registry
from drivers.storages.memory.backend import MemoryBackend

storage_registry.register("memory", MemoryBackend)
