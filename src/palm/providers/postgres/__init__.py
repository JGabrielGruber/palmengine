"""Postgres provider app."""

from palm.providers.postgres import registry as registry
from palm.providers.postgres.provider import PostgresProvider

__all__ = ["PostgresProvider", "registry"]
