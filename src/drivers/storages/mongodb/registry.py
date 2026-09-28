"""Mongodb storage registration."""

from palm.core.registry import storage_registry
from drivers.storages.mongodb.backend import MongoStorageBackend

storage_registry.register("mongodb", MongoStorageBackend)
