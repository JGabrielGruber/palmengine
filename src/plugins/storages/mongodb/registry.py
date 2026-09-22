"""Mongodb storage registration."""

from palm.core.registry import storage_registry
from plugins.storages.mongodb.backend import MongoStorageBackend

storage_registry.register("mongodb", MongoStorageBackend)
