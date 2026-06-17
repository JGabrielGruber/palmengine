"""Tests for ResourceEngine invoke, param binding, and provider contract."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.common import DefinitionRepository
from palm.common.resource import resource_definition_resolver
from palm.core.event import EventEngine
from palm.core.resource import (
    ProviderResult,
    ResourceEngine,
    ResolvedResourceSpec,
    bind_resource_id,
    bind_resource_params,
    bind_resource_value,
)
from palm.definitions import ResourceDefinition
from palm.providers.rest.provider import RestProvider
from palm.states import BlackboardState


def _fetch_customer_definition() -> ResourceDefinition:
    return ResourceDefinition(
        id="resource-fetch-customer",
        name="fetch-customer",
        provider="rest",
        action="fetch",
        resource_id="customers/{customer_id}",
        params={"customer_id": "{{ state.customer_id }}"},
    )


def test_bind_resource_value_state_placeholder() -> None:
    state = {"customer_id": "cust-42"}
    assert bind_resource_value("{{ state.customer_id }}", state) == "cust-42"
    assert bind_resource_value("customers/{{ state.customer_id }}", state) == "customers/cust-42"


def test_bind_resource_id_param_placeholder() -> None:
    bound = bind_resource_id(
        "customers/{customer_id}",
        {"customer_id": "cust-42"},
    )
    assert bound == "customers/cust-42"


def test_bind_resource_params_nested() -> None:
    state = BlackboardState({"tenant": "acme"})
    bound = bind_resource_params(
        {"tenant": "{{ state.tenant }}", "nested": {"id": "{{ state.tenant }}"}},
        state,
    )
    assert bound == {"tenant": "acme", "nested": {"id": "acme"}}


def test_rest_provider_invoke_fetch() -> None:
    provider = RestProvider(name="rest")
    provider.connect()
    result = provider.invoke("fetch", resource_id="users/1", params={"limit": 5})
    provider.disconnect()
    assert result.success is True
    assert result.data["id"] == "users/1"
    assert result.data["source"] == "rest"
    assert result.data["params"]["limit"] == 5


def test_rest_provider_describe_and_health() -> None:
    provider = RestProvider(name="rest")
    descriptor = provider.describe()
    health = provider.health()
    assert descriptor.name == "rest"
    assert any(action.name == "fetch" for action in descriptor.actions)
    assert health.healthy is True


def test_resource_engine_direct_provider_invoke() -> None:
    engine = ResourceEngine()
    engine.initialize()
    result = engine.invoke(
        provider="rest",
        action="fetch",
        resource_id="health/check",
        params={"probe": True},
    )
    engine.shutdown()
    assert result.success is True
    assert result.data["source"] == "rest"


def test_resource_engine_invoke_via_definition_ref() -> None:
    repo = DefinitionRepository()
    repo.register_resource(_fetch_customer_definition())
    engine = ResourceEngine()
    engine.initialize(definition_resolver=resource_definition_resolver(repo))
    result = engine.invoke(
        "fetch-customer",
        state={"customer_id": "cust-99"},
    )
    engine.shutdown()
    assert result.success is True
    assert result.data["id"] == "customers/cust-99"
    assert result.metadata["definition_name"] == "fetch-customer"
    assert result.metadata["provider"] == "rest"


def test_resource_engine_emits_events() -> None:
    events: list[str] = []
    event_engine = EventEngine()
    event_engine.initialize()
    event_engine.subscribe("resource.invoked", lambda event: events.append(event.type))
    event_engine.subscribe("resource.completed", lambda event: events.append(event.type))

    engine = ResourceEngine()
    engine.initialize(event_engine=event_engine)
    result = engine.invoke(provider="rest", action="fetch", resource_id="x")
    engine.shutdown()
    event_engine.shutdown()

    assert result.success is True
    assert events == ["resource.invoked", "resource.completed"]


def test_resource_engine_failed_invoke_emits_failed_event() -> None:
    events: list[dict] = []
    event_engine = EventEngine()
    event_engine.initialize()
    event_engine.subscribe(
        "resource.failed",
        lambda event: events.append(event.payload),
    )

    engine = ResourceEngine()
    engine.initialize(event_engine=event_engine)
    result = engine.invoke(provider="rest", action="unknown")
    engine.shutdown()
    event_engine.shutdown()

    assert result.success is False
    assert events
    assert events[0]["action"] == "unknown"


def test_resource_engine_missing_resolver_for_ref() -> None:
    engine = ResourceEngine()
    engine.initialize()
    result = engine.invoke("fetch-customer")
    engine.shutdown()
    assert result.success is False
    assert "resolver" in (result.error or "").lower()


def test_resource_engine_unknown_definition() -> None:
    repo = DefinitionRepository()
    engine = ResourceEngine()
    engine.initialize(definition_resolver=resource_definition_resolver(repo))
    result = engine.invoke("missing-resource")
    engine.shutdown()
    assert result.success is False
    assert "not found" in (result.error or "").lower()


def test_resolved_resource_spec_from_repository() -> None:
    repo = DefinitionRepository()
    repo.register_resource(_fetch_customer_definition())
    resolve = resource_definition_resolver(repo)
    spec = resolve("fetch-customer")
    assert isinstance(spec, ResolvedResourceSpec)
    assert spec.provider == "rest"
    assert spec.resource_id == "customers/{customer_id}"


def test_provider_result_helpers() -> None:
    ok = ProviderResult.ok({"id": 1}, provider="rest")
    fail = ProviderResult.fail("boom", provider="rest")
    assert ok.success and ok.data == {"id": 1}
    assert not fail.success and fail.error == "boom"