"""Mongodb storage app — MongoDB persistence backend (stub)."""

from plugins.storages.mongodb import registry as registry
from plugins.storages.mongodb.backend import MongoStorageBackend

__all__ = ["MongoStorageBackend", "registry"]
