"""
Abstract resource provider contract.

Concrete providers (REST, GraphQL, Postgres) live in ``palm.providers``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from palm.core.resource.result import (
    ProviderActionDescriptor,
    ProviderDescriptor,
    ProviderHealth,
    ProviderResult,
)


class BaseProvider(ABC):
    """Abstract external resource accessor with action-based invocation."""

    def __init__(self, *, name: str) -> None:
        self.name = name

    @abstractmethod
    def connect(self) -> None:
        """Establish or validate the provider connection."""

    @abstractmethod
    def fetch(self, resource_id: str, **params: Any) -> Any:
        """Retrieve a resource by identifier."""

    @abstractmethod
    def disconnect(self) -> None:
        """Release provider resources."""

    def invoke(
        self,
        action: str,
        *,
        params: dict[str, Any] | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        """Execute a named action and return a structured result."""
        bound = dict(params or {})
        if resource_id is not None:
            bound.setdefault("resource_id", resource_id)
        if action == "fetch":
            rid = bound.pop("resource_id", resource_id or "")
            try:
                data = self.fetch(str(rid), **bound, **kwargs)
            except Exception as exc:
                return ProviderResult.fail(
                    str(exc),
                    action=action,
                    provider=self.name,
                    resource_id=str(rid),
                )
            return ProviderResult.ok(
                data,
                action=action,
                provider=self.name,
                resource_id=str(rid),
            )
        return ProviderResult.fail(
            f"Unsupported action {action!r}",
            action=action,
            provider=self.name,
        )

    def describe(self) -> ProviderDescriptor:
        """Return action metadata for catalogs and diagnostics."""
        return ProviderDescriptor(
            name=self.name,
            description=f"{self.name} resource provider",
            actions=(
                ProviderActionDescriptor(
                    "fetch",
                    "Retrieve a resource by identifier",
                ),
            ),
        )

    def health(self) -> ProviderHealth:
        """Return a lightweight connectivity signal."""
        return ProviderHealth(healthy=True, message="connected")
