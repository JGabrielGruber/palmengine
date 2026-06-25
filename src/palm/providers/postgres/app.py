"""Postgres provider app manifest."""

from __future__ import annotations

from palm.common.providers.app import ProviderApp


class PostgresApp(ProviderApp):
    name = "postgres"
    label = "PostgreSQL resource access"
    palm_layers = ("core.resource",)
    actions = ("fetch",)
    registry_hooks = ("provider_registry",)


postgres_app = PostgresApp()

__all__ = ["PostgresApp", "postgres_app"]