"""Fetch external resources and merge results into payloads."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.resource.observability import resource_correlation
from palm.core.transform.base import BaseTransformRule, TransformContext


class EnrichResourceRule(BaseTransformRule):
    """
    Call :class:`~palm.core.resource.ResourceEngine` to enrich a payload.

    Options:

    - ``resource_ref`` — resolved :class:`~palm.definitions.ResourceDefinition` name or id
    - ``provider`` — registered provider name (direct invoke when ``resource_ref`` omitted)
    - ``action`` — provider action (default ``fetch`` for direct provider; definition default for ref)
    - ``params`` — invoke params with optional ``{{ state.key }}`` binding
    - ``resource_id`` — explicit id, or read from mapping via ``id_field`` (default ``id``)
    - ``merge`` — when true (default), merge fetch result under ``target_field``
    - ``target_field`` — key for merged resource data (default ``resource``)
    - ``resource_engine`` — injected by TransformLeaf / wizard runtime
    """

    name: ClassVar[str] = "enrich_resource"

    @classmethod
    def from_options(cls, **options: Any) -> EnrichResourceRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        engine = options.get("resource_engine")
        if engine is None:
            raise TransformApplicationError(
                f"{self.rule_name} requires resource_engine (configure runtime ResourceEngine)",
            )
        resource_ref = options.get("resource_ref")
        provider_name = options.get("provider")
        if not resource_ref and not provider_name:
            raise TransformApplicationError(
                f"{self.rule_name} requires provider= or resource_ref=",
            )

        value = context.value
        state = value if isinstance(value, dict) else {}
        id_field = str(options.get("id_field", "id"))
        resource_id = options.get("resource_id")
        action = options.get("action")
        params = dict(options.get("params") or {})
        correlation = resource_correlation(state if isinstance(state, dict) else None)

        if resource_ref is None:
            if resource_id is None:
                if isinstance(value, dict) and id_field in value:
                    resource_id = value[id_field]
                elif isinstance(value, str):
                    resource_id = value
                else:
                    raise TransformApplicationError(
                        f"{self.rule_name} requires resource_id= or mapping with {id_field!r}",
                    )
            invoke_result = engine.invoke(
                provider=str(provider_name),
                action=str(action or "fetch"),
                resource_id=str(resource_id),
                params=params,
                state=state,
                correlation=correlation,
            )
        else:
            invoke_kwargs: dict[str, Any] = {
                "resource_ref": str(resource_ref),
                "state": state,
                "correlation": correlation,
            }
            if action is not None:
                invoke_kwargs["action"] = str(action)
            if params:
                invoke_kwargs["params"] = params
            if resource_id is not None:
                invoke_kwargs["resource_id"] = str(resource_id)
            invoke_result = engine.invoke(**invoke_kwargs)
            resource_id = invoke_result.metadata.get("resource_id", resource_id)
            provider_name = invoke_result.metadata.get("provider", provider_name)

        if not invoke_result.success:
            raise TransformApplicationError(
                invoke_result.error or f"{self.rule_name} invocation failed",
            )
        fetched = invoke_result.data
        merge = bool(options.get("merge", True))
        target_field = str(options.get("target_field", "resource"))

        if merge and isinstance(value, dict):
            out = dict(value)
            out[target_field] = fetched
            result = out
        else:
            result = fetched

        return context.advance(
            self.rule_name,
            result,
            meta={
                "provider": provider_name,
                "resource_ref": resource_ref,
                "resource_id": str(resource_id) if resource_id is not None else None,
                "action": invoke_result.metadata.get("action", action),
                "target_field": target_field if merge else None,
            },
        )