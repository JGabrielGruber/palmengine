"""Tiered storage — hot map on the instance, write-through to a cold backend."""

from drivers.storages.tiered import registry as registry
from drivers.storages.tiered.backend import TieredBackend

__all__ = ["TieredBackend", "registry"]
