"""Postgres resource provider — relational data access (placeholder)."""

from __future__ import annotations

from typing import Any

from palm.core.resource import BaseProvider


class PostgresProvider(BaseProvider):
    """Intention stub — not a live SQL provider (docs/STUBS.md ST-001)."""

    def connect(self) -> None:
        raise NotImplementedError(
            "postgres provider is an intention stub (docs/STUBS.md ST-001); "
            "not in default INSTALLED_PROVIDERS"
        )

    def fetch(self, resource_id: str, **params: Any) -> Any:
        raise NotImplementedError(
            "postgres provider is an intention stub (docs/STUBS.md ST-001); "
            f"refused fetch for {resource_id!r}"
        )

    def disconnect(self) -> None:
        pass
