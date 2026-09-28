"""Postgres storage registration."""

from palm.core.registry import storage_registry
from drivers.storages.postgres.backend import PostgresStorageBackend

storage_registry.register("postgres", PostgresStorageBackend)
