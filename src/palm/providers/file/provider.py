"""File document resource provider — path-shaped local documents."""

from __future__ import annotations

from typing import Any

from palm.core.resource import BaseProvider
from palm.core.resource.result import ProviderDescriptor, ProviderHealth, ProviderResult
from palm.providers.file.bindings.resource.descriptor import describe
from palm.providers.file.bindings.resource.invoke import invoke_action


class FileProvider(BaseProvider):
    """Read/write documents under a host ``documents_root`` directory."""

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        merged = dict(params)
        result = self.invoke("read", resource_id=resource_id, params=merged)
        if not result.success:
            raise RuntimeError(result.error or "read failed")
        payload = result.data if isinstance(result.data, dict) else {}
        return payload.get("content")

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
        return ProviderHealth(healthy=True, message="file provider ready")


__all__ = ["FileProvider"]