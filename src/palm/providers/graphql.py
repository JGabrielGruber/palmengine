"""
GraphQL resource provider — schema-driven API access (placeholder).
"""

from __future__ import annotations

from typing import Any

from palm.core.registry import provider_registry
from palm.core.resource import BaseProvider


class GraphqlProvider(BaseProvider):
    """Stub GraphQL provider."""

    def connect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        return {"id": resource_id, "source": "graphql", "params": params}

    def disconnect(self) -> None:
        pass


provider_registry.register("graphql", GraphqlProvider)
