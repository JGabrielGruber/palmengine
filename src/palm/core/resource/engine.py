"""
Resource engine — coordinates external data providers.

Resolves providers by name from ``provider_registry``. Optional definition
resolution and event emission are injected at initialize time so core stays
free of outer Palm packages.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.registry import provider_registry
from palm.core.resource.base_provider import BaseProvider
from palm.core.resource.cache import (
    ResourceCacheConfig,
    TtlCache,
    definition_cache_key,
    result_cache_key,
)
from palm.core.resource.invocation import (
    ResolvedResourceSpec,
    bind_resource_id,
    bind_resource_params,
)
from palm.core.resource.result import ProviderResult

DefinitionResolver = Callable[[str], ResolvedResourceSpec]
EventPublisher = Callable[[str, dict[str, Any]], None]


class ResourceEngine(BasePalmEngine):
    """Manages provider lifecycle, definition-aware invocation, and events."""

    def __init__(self) -> None:
        super().__init__(name="resource")
        self._active: dict[str, BaseProvider] = {}
        self._definition_resolver: DefinitionResolver | None = None
        self._publish_event: EventPublisher | None = None
        self._cache_config = ResourceCacheConfig()
        self._definition_cache: TtlCache | None = None
        self._result_cache: TtlCache | None = None

    def use(self, name: str) -> BaseProvider:
        """Return a connected provider instance for ``name``."""
        if name not in self._active:
            cls = provider_registry.get(name)
            provider = cls(name=name)
            provider.connect()
            self._active[name] = provider
        return self._active[name]

    def invoke(
        self,
        resource_ref: str | None = None,
        *,
        provider: str | None = None,
        action: str | None = None,
        params: dict[str, Any] | None = None,
        state: Any = None,
        resource_id: str | None = None,
        correlation: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        """
        Invoke a provider action directly or via a resolved resource definition.

        When ``resource_ref`` is set, the injected definition resolver supplies
        provider, default action, ``resource_id``, and param templates. Caller
        ``params`` and ``action`` override definition defaults. ``state`` binds
        ``{{ state.key }}`` placeholders in params and ``resource_id``.
        """
        if not self.is_initialized:
            return ProviderResult.fail("ResourceEngine is not initialized")

        spec_provider = provider
        spec_action = action or "fetch"
        spec_params = dict(params or {})
        spec_resource_id = resource_id
        definition_id: str | None = None
        definition_name: str | None = None

        if resource_ref is not None:
            if self._definition_resolver is None:
                result = ProviderResult.fail(
                    "Definition resolver is not configured",
                    resource_ref=resource_ref,
                )
                self._emit(
                    "resource.failed",
                    resource_ref=resource_ref,
                    error=result.error,
                )
                return result
            try:
                spec = self._resolve_definition(resource_ref)
            except Exception as exc:
                result = ProviderResult.fail(
                    str(exc),
                    resource_ref=resource_ref,
                )
                self._emit(
                    "resource.failed",
                    resource_ref=resource_ref,
                    error=result.error,
                )
                return result
            spec_provider = spec.provider
            spec_action = action or spec.action
            definition_id = spec.definition_id
            definition_name = spec.name
            spec_resource_id = spec_resource_id or spec.resource_id
            merged = dict(spec.params)
            merged.update(spec_params)
            spec_params = merged

        if not spec_provider:
            result = ProviderResult.fail("provider or resource_ref is required")
            self._emit("resource.failed", error=result.error, resource_ref=resource_ref)
            return result

        bound_params = bind_resource_params(spec_params, state)
        bound_resource_id = bind_resource_id(spec_resource_id, bound_params, state)

        cached = self._cached_result(
            provider=spec_provider,
            action=spec_action,
            resource_ref=resource_ref,
            resource_id=bound_resource_id,
            params=bound_params,
        )
        if cached is not None:
            return cached

        event_base = {
            "provider": spec_provider,
            "action": spec_action,
            "resource_ref": resource_ref,
            "definition_id": definition_id,
            "definition_name": definition_name,
            "resource_id": bound_resource_id,
            "params": bound_params,
            "mutating": spec_action not in {"fetch", "health", "describe"},
        }
        if correlation:
            event_base.update(
                {key: value for key, value in correlation.items() if value is not None}
            )
        self._emit("resource.invoked", **event_base)

        try:
            prov = self.use(spec_provider)
            result = prov.invoke(
                spec_action,
                params=bound_params,
                resource_id=bound_resource_id,
                **kwargs,
            )
        except Exception as exc:
            result = ProviderResult.fail(
                str(exc),
                provider=spec_provider,
                action=spec_action,
            )
            self._emit("resource.failed", error=result.error, **event_base)
            return result

        metadata = {
            **result.metadata,
            "provider": spec_provider,
            "action": spec_action,
            "resource_ref": resource_ref,
            "definition_id": definition_id,
            "definition_name": definition_name,
            "resource_id": bound_resource_id,
        }
        correlation = _correlation_payload(result)
        if result.success:
            final = ProviderResult.ok(result.data, **metadata)
            self._store_result_cache(
                provider=spec_provider,
                action=spec_action,
                resource_ref=resource_ref,
                resource_id=bound_resource_id,
                params=bound_params,
                result=final,
            )
            self._emit("resource.completed", **event_base, **correlation)
            return final
        self._emit(
            "resource.failed",
            error=result.error,
            **event_base,
            **correlation,
        )
        return ProviderResult.fail(
            result.error or "invoke failed",
            **metadata,
        )

    def clear_caches(self) -> None:
        """Drop cached definitions and results."""
        if self._definition_cache is not None:
            self._definition_cache.clear()
        if self._result_cache is not None:
            self._result_cache.clear()

    def _resolve_definition(self, resource_ref: str) -> ResolvedResourceSpec:
        if self._definition_cache is not None:
            cached = self._definition_cache.get(definition_cache_key(resource_ref))
            if cached is not None:
                return cached
        assert self._definition_resolver is not None
        spec = self._definition_resolver(resource_ref)
        if self._definition_cache is not None:
            self._definition_cache.set(definition_cache_key(resource_ref), spec)
        return spec

    def _cached_result(
        self,
        *,
        provider: str,
        action: str,
        resource_ref: str | None,
        resource_id: str | None,
        params: dict[str, Any],
    ) -> ProviderResult | None:
        if self._result_cache is None or action not in self._cache_config.cacheable_actions:
            return None
        key = result_cache_key(
            provider=provider,
            action=action,
            resource_ref=resource_ref,
            resource_id=resource_id,
            params=params,
        )
        cached = self._result_cache.get(key)
        return cached if isinstance(cached, ProviderResult) else None

    def _store_result_cache(
        self,
        *,
        provider: str,
        action: str,
        resource_ref: str | None,
        resource_id: str | None,
        params: dict[str, Any],
        result: ProviderResult,
    ) -> None:
        if self._result_cache is None or action not in self._cache_config.cacheable_actions:
            return
        key = result_cache_key(
            provider=provider,
            action=action,
            resource_ref=resource_ref,
            resource_id=resource_id,
            params=params,
        )
        self._result_cache.set(key, result)

    def _do_initialize(self, **options: Any) -> None:
        resolver = options.get("definition_resolver")
        if callable(resolver):
            self._definition_resolver = resolver
        publisher = options.get("event_publisher")
        if callable(publisher):
            self._publish_event = publisher
        else:
            event_engine = options.get("event_engine")
            if event_engine is not None and hasattr(event_engine, "emit"):

                def _publish(event_type: str, payload: dict[str, Any]) -> None:
                    event_engine.emit(event_type, **payload)

                self._publish_event = _publish

        cache_config = options.get("resource_cache")
        if isinstance(cache_config, ResourceCacheConfig):
            self._cache_config = cache_config
        elif isinstance(cache_config, dict):
            self._cache_config = ResourceCacheConfig(**cache_config)

        if self._cache_config.cache_definitions:
            self._definition_cache = TtlCache(
                max_entries=self._cache_config.max_entries,
                ttl_seconds=self._cache_config.ttl_seconds,
            )
        if self._cache_config.cache_results:
            self._result_cache = TtlCache(
                max_entries=self._cache_config.max_entries,
                ttl_seconds=self._cache_config.ttl_seconds,
            )

    def _do_shutdown(self) -> None:
        for provider in self._active.values():
            provider.disconnect()
        self._active.clear()
        self._definition_resolver = None
        self._publish_event = None
        self.clear_caches()
        self._definition_cache = None
        self._result_cache = None

    def _emit(self, event_type: str, **payload: Any) -> None:
        if self._publish_event is None:
            return
        self._publish_event(event_type, payload)


def _correlation_payload(result: ProviderResult) -> dict[str, Any]:
    """Extract compositional correlation fields for observability events."""
    payload: dict[str, Any] = {}
    for key in ("invoke_depth", "parent_job_id", "mode"):
        if key in result.metadata:
            payload[key] = result.metadata[key]
    if isinstance(result.data, dict):
        chain = result.data.get("invoke_chain")
        if chain is not None:
            payload["invoke_chain"] = chain
    return payload
