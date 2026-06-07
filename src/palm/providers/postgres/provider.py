"""Postgres resource provider — relational data access (placeholder)."""

from __future__ import annotations

from typing import Any

from palm.core.resource import BaseProvider


class PostgresProvider(BaseProvider):
    """Stub postgres provider."""

    def connect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        return {"id": resource_id, "source": "postgres", "params": params}

    def disconnect(self) -> None:
        pass
