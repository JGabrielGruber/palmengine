"""Postgres storage registration."""

from palm.core.registry import storage_registry
from plugins.storages.postgres.backend import PostgresStorageBackend

storage_registry.register("postgres", PostgresStorageBackend)
