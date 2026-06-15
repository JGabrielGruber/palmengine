"""Fetch external resources and merge results into payloads."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext


class EnrichResourceRule(BaseTransformRule):
    """
    Call :class:`~palm.core.resource.ResourceEngine` to enrich a payload.

    Options:

    - ``provider`` — registered provider name (required)
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
        provider_name = options.get("provider")
        if not provider_name:
            raise TransformApplicationError(f"{self.rule_name} requires provider=")

        value = context.value
        id_field = str(options.get("id_field", "id"))
        resource_id = options.get("resource_id")
        if resource_id is None:
            if isinstance(value, dict) and id_field in value:
                resource_id = value[id_field]
            elif isinstance(value, str):
                resource_id = value
            else:
                raise TransformApplicationError(
                    f"{self.rule_name} requires resource_id= or mapping with {id_field!r}",
                )

        provider = engine.use(str(provider_name))
        fetched = provider.fetch(str(resource_id))
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
                "resource_id": str(resource_id),
                "target_field": target_field if merge else None,
            },
        )
