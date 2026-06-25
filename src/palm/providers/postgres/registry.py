"""Postgres provider registration."""

from palm.core.registry import provider_registry
from palm.providers.postgres.app import postgres_app
from palm.providers.postgres.provider import PostgresProvider

provider_registry.register("postgres", PostgresProvider)
postgres_app.register()
