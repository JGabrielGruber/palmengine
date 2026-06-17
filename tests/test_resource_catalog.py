"""Tests for ResourceCatalog discovery."""

from __future__ import annotations

import palm.providers  # noqa: F401 — register providers
from palm.common import DefinitionRepository
from palm.common.resource.catalog import ResourceCatalog
from palm.definitions import ResourceDefinition


def test_resource_catalog_entry_includes_provider_actions() -> None:
    repo = DefinitionRepository()
    repo.register_resource(
        ResourceDefinition(
            id="resource-fetch-customer",
            name="fetch-customer",
            provider="rest",
            action="fetch",
            resource_id="customers/{customer_id}",
            params={"customer_id": "{{ state.customer_id }}"},
            input_schema={"type": "object"},
        ),
    )
    catalog = ResourceCatalog(repo)
    entries = catalog.entries()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.provider == "rest"
    assert entry.action == "fetch"
    assert "fetch" in entry.provider_actions
    assert entry.has_input_schema is True
    assert "customers" in entry.summary()


def test_resource_catalog_describe_payload() -> None:
    repo = DefinitionRepository()
    repo.register_resource(
        ResourceDefinition(
            name="rest-health",
            provider="rest",
            action="fetch",
            resource_id="health/check",
        ),
    )
    payload = ResourceCatalog(repo).describe("rest-health")
    assert payload["name"] == "rest-health"
    assert payload["provider"] == "rest"
    assert payload["resource_id"] == "health/check"
    assert "provider_actions" in payload


def test_definition_repository_find_resources() -> None:
    repo = DefinitionRepository()
    repo.register_resource(
        ResourceDefinition(name="alpha-rest", provider="rest", action="fetch"),
    )
    repo.register_resource(
        ResourceDefinition(name="beta-palm", provider="palm", action="submit_flow"),
    )
    assert len(repo.find_resources("palm")) == 1
    assert repo.list_resources_by_provider("rest")[0].name == "alpha-rest"