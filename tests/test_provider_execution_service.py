"""Unit tests for ProviderExecutionService.invoke."""

from __future__ import annotations

from typing import Any

import pytest

from palm.common.cqrs import CommandBus
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.core.resource.result import ProviderResult
from palm.services.execution.providers.service import ProviderExecutionService


class _DefinitionsStub:
    def __init__(self, provider: str) -> None:
        self._provider = provider

    def get_resource(self, resource_ref: str) -> dict[str, Any]:
        if resource_ref != "echo":
            raise DefinitionNotFoundServiceError("resource", resource_ref)
        return {"provider": self._provider, "name": resource_ref}


class _EngineStub:
    is_initialized = True

    def initialize(self) -> None:
        return None

    def invoke(self, resource_ref: str, **kwargs: Any) -> ProviderResult:
        return ProviderResult.ok({"resource_ref": resource_ref, **kwargs})


class _RuntimeStub:
    def __init__(self) -> None:
        self.resource = _EngineStub()


def test_provider_invoke_validates_provider_name() -> None:
    service = ProviderExecutionService(
        commands=CommandBus(),
        queries=object(),
        schemas=CqrsSchemaRegistry(),
        runtime=_RuntimeStub(),
        definitions=_DefinitionsStub("rest"),
    )
    with pytest.raises(ValueError, match="owned by provider"):
        service.invoke("echo", provider="palm")


def test_provider_invoke_returns_result_envelope() -> None:
    service = ProviderExecutionService(
        commands=CommandBus(),
        queries=object(),
        schemas=CqrsSchemaRegistry(),
        runtime=_RuntimeStub(),
        definitions=_DefinitionsStub("rest"),
    )
    payload = service.invoke("echo", provider="rest", params={"x": 1})
    assert payload["success"] is True
    assert payload["data"]["resource_ref"] == "echo"