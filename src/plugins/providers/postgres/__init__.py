"""Postgres provider app."""

from plugins.providers.postgres import registry as registry
from plugins.providers.postgres.provider import PostgresProvider

__all__ = ["PostgresProvider", "registry"]
