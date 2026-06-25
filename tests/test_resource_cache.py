"""Tests for ResourceEngine optional caching."""

from __future__ import annotations

import palm.providers  # noqa: F401 — register providers
from palm.common import DefinitionRepository
from palm.common.resource import resource_definition_resolver
from palm.core.resource import ResourceEngine
from palm.core.resource.cache import ResourceCacheConfig
from palm.definitions import ResourceDefinition


def test_resource_engine_caches_fetch_results_when_enabled(rest_base_url: str) -> None:
    repo = DefinitionRepository()
    repo.register_resource(
        ResourceDefinition(
            name="rest-health",
            provider="rest",
            action="fetch",
            resource_id="health/check",
            params={"base_url": rest_base_url},
        ),
    )
    engine = ResourceEngine()
    engine.initialize(
        definition_resolver=resource_definition_resolver(repo),
        resource_cache=ResourceCacheConfig(
            cache_definitions=True,
            cache_results=True,
            ttl_seconds=30.0,
            max_entries=16,
        ),
    )
    first = engine.invoke("rest-health")
    second = engine.invoke("rest-health")
    engine.shutdown()
    assert first.success is True
    assert second.success is True
    assert first.data == second.data


def test_resource_engine_definition_cache_avoids_repeated_resolve(rest_base_url: str) -> None:
    repo = DefinitionRepository()
    repo.register_resource(
        ResourceDefinition(
            name="rest-health",
            provider="rest",
            action="fetch",
            resource_id="health/check",
            params={"base_url": rest_base_url},
        ),
    )
    calls = {"count": 0}
    base = resource_definition_resolver(repo)

    def counting_resolver(ref: str):
        calls["count"] += 1
        return base(ref)

    engine = ResourceEngine()
    engine.initialize(
        definition_resolver=counting_resolver,
        resource_cache=ResourceCacheConfig(cache_definitions=True, cache_results=False),
    )
    engine.invoke("rest-health")
    engine.invoke("rest-health")
    engine.shutdown()
    assert calls["count"] == 1
