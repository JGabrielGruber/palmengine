"""Tiered storage registration."""

from drivers.storages.tiered.backend import TieredBackend
from palm.core.registry import storage_registry

storage_registry.register("tiered", TieredBackend)
