"""Postgres storage app — Stub Postgres persistence backend."""

from drivers.storages.postgres import registry as registry
from drivers.storages.postgres.backend import PostgresStorageBackend

__all__ = ["PostgresStorageBackend", "registry"]
