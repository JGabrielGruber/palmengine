"""Postgres storage app — Stub Postgres persistence backend."""

from plugins.storages.postgres import registry as registry
from plugins.storages.postgres.backend import PostgresStorageBackend

__all__ = ["PostgresStorageBackend", "registry"]
