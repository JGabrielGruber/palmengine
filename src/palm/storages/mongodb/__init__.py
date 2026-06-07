"""Mongodb storage app — MongoDB persistence backend (stub)."""

from palm.storages.mongodb import registry as registry
from palm.storages.mongodb.backend import MongoStorageBackend

__all__ = ["MongoStorageBackend", "registry"]
