"""REST resource provider — HTTP API access (placeholder)."""

from __future__ import annotations

from typing import Any

from palm.core.resource import BaseProvider
from palm.core.resource.result import ProviderActionDescriptor, ProviderDescriptor


class RestProvider(BaseProvider):
    """Stub rest provider."""

    def connect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        return {"id": resource_id, "source": "rest", "params": params}

    def disconnect(self) -> None:
        pass

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name=self.name,
            description="HTTP REST resource access",
            actions=(ProviderActionDescriptor("fetch", "GET a resource by path or id"),),
        )
