"""GraphQL resource provider — schema-driven API access (placeholder)."""

from __future__ import annotations

from typing import Any

from palm.core.resource import BaseProvider


class GraphqlProvider(BaseProvider):
    """Stub graphql provider."""

    def connect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        return {"id": resource_id, "source": "graphql", "params": params}

    def disconnect(self) -> None:
        pass
