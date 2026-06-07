"""Postgres storage app — Stub Postgres persistence backend."""

from palm.storages.postgres import registry as registry
from palm.storages.postgres.backend import PostgresStorageBackend

__all__ = ["PostgresStorageBackend", "registry"]
