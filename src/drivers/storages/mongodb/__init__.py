"""Mongodb storage app — MongoDB persistence backend (stub)."""

from drivers.storages.mongodb import registry as registry
from drivers.storages.mongodb.backend import MongoStorageBackend

__all__ = ["MongoStorageBackend", "registry"]
