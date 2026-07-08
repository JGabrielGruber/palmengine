"""KV resource provider — local key-value storage for flow-owned data."""

from __future__ import annotations

from typing import Any

from palm.core.resource import BaseProvider
from palm.core.resource.result import ProviderDescriptor, ProviderHealth, ProviderResult
from palm.providers.kv.bindings.resource.descriptor import describe
from palm.providers.kv.bindings.resource.invoke import invoke_action


class KvProvider(BaseProvider):
    """Read/write JSON-compatible values by logical key."""

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        merged = dict(params)
        merged.setdefault("backend", "auto")
        result = self.invoke("get", resource_id=resource_id, params=merged)
        if not result.success:
            raise RuntimeError(result.error or "get failed")
        payload = result.data if isinstance(result.data, dict) else {}
        if payload.get("found"):
            return payload.get("value")
        return payload.get("value")

    def invoke(
        self,
        action: str,
        *,
        params: dict[str, Any] | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        merged = dict(params or {})
        merged.update(kwargs)
        return invoke_action(
            name=self.name,
            action=action,
            params=merged,
            resource_id=resource_id,
        )

    def describe(self) -> ProviderDescriptor:
        return describe(name=self.name)

    def health(self) -> ProviderHealth:
        return ProviderHealth(healthy=True, message="kv provider ready")


__all__ = ["KvProvider"]