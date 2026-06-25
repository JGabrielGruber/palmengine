"""Palm resource provider — compositional orchestration (Palm calling Palm)."""

from __future__ import annotations

from typing import Any

from palm.core.resource import BaseProvider
from palm.core.resource.result import ProviderDescriptor, ProviderHealth, ProviderResult
from palm.providers.palm.bindings.resource.descriptor import describe, health
from palm.providers.palm.bindings.resource.invoke import invoke_action
from palm.providers.palm.flow.coordinator import PalmInvokeCoordinator


class PalmProvider(BaseProvider):
    """Invoke Palm flows, processes, and resources locally or via Server HTTP."""

    def __init__(
        self,
        *,
        name: str,
        coordinator: PalmInvokeCoordinator | None = None,
    ) -> None:
        super().__init__(name=name)
        self._coordinator = coordinator or PalmInvokeCoordinator()

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def fetch(self, resource_id: str, **params: Any) -> Any:
        """Fetch a job snapshot by id (``fetch`` action alias)."""
        result = self.invoke("fetch", resource_id=resource_id, params=dict(params))
        if not result.success:
            raise RuntimeError(result.error or "fetch failed")
        return result.data

    def invoke(
        self,
        action: str,
        *,
        params: dict[str, Any] | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        execution_state = kwargs.pop("state", None)
        return invoke_action(
            self._coordinator,
            name=self.name,
            action=action,
            params=params,
            resource_id=resource_id,
            execution_state=execution_state,
            **kwargs,
        )

    def describe(self) -> ProviderDescriptor:
        return describe(name=self.name)

    def health(self) -> ProviderHealth:
        return health()