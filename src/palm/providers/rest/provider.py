"""REST resource provider — HTTP API access."""

from __future__ import annotations

from typing import Any

from palm.core.resource import BaseProvider
from palm.core.resource.result import ProviderDescriptor, ProviderHealth, ProviderResult
from palm.providers.rest.bindings.resource.descriptor import describe
from palm.providers.rest.bindings.resource.invoke import fetch_resource, invoke_action
from palm.providers.rest.flow.params import RestInvokeParams


class RestProvider(BaseProvider):
    """HTTP REST resource provider."""

    def __init__(self, *, name: str, base_url: str | None = None) -> None:
        super().__init__(name=name)
        self._base_url = base_url

    def connect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        merged = dict(params)
        if self._base_url and "base_url" not in merged:
            merged["base_url"] = self._base_url
        result = fetch_resource(name=self.name, resource_id=resource_id, params=merged)
        if not result.success:
            raise RuntimeError(result.error or "fetch failed")
        return result.data

    def disconnect(self) -> None:
        pass

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
        if self._base_url and "base_url" not in merged:
            merged["base_url"] = self._base_url
        return invoke_action(
            name=self.name,
            action=action,
            params=merged,
            resource_id=resource_id,
        )

    def describe(self) -> ProviderDescriptor:
        return describe(name=self.name)

    def health(self) -> ProviderHealth:
        if not self._base_url:
            return ProviderHealth(healthy=True, message="rest provider ready (no base_url configured)")
        try:
            RestInvokeParams.from_mapping({"base_url": self._base_url}).resolve_url("")
            return ProviderHealth(healthy=True, message=f"base_url configured: {self._base_url}")
        except ValueError as exc:
            return ProviderHealth(healthy=False, message=str(exc))