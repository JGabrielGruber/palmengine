"""Persist blackboard data via ResourceEngine (pipeline-friendly put)."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.resource.observability import resource_correlation
from palm.core.transform.base import BaseTransformRule, TransformContext


class PutResourceRule(BaseTransformRule):
    """
    Invoke a resource action (default ``put``) with ``context.value``.

    Options: ``resource`` or ``resource_ref``, ``action`` (default ``put``), ``params``.
    """

    name: ClassVar[str] = "put_resource"

    @classmethod
    def from_options(cls, **options: Any) -> PutResourceRule:
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

        resource_ref = options.get("resource") or options.get("resource_ref")
        if not resource_ref:
            raise TransformApplicationError(f"{self.rule_name} requires resource= or resource_ref=")

        action = str(options.get("action", "put"))
        params = dict(options.get("params") or {})
        value = context.value
        value_key = options.get("value_key")
        if value_key and isinstance(value, dict):
            nested = value.get(str(value_key))
            if nested is not None:
                value = nested

        if action == "put" and "value" not in params:
            params["value"] = value

        state = value if isinstance(value, dict) else {}
        correlation = resource_correlation(state if isinstance(state, dict) else None)
        invoke_result = engine.invoke(
            resource_ref=str(resource_ref),
            action=action,
            params=params,
            state=state,
            correlation=correlation,
        )
        if not invoke_result.success:
            raise TransformApplicationError(
                invoke_result.error or f"{self.rule_name} invocation failed",
            )

        if action == "put":
            result_value = value
        else:
            result_value = invoke_result.data if invoke_result.data is not None else value
        return context.advance(
            self.rule_name,
            result_value,
            meta={
                "resource_ref": str(resource_ref),
                "action": invoke_result.metadata.get("action", action),
                "resource_id": invoke_result.metadata.get("resource_id"),
            },
        )


__all__ = ["PutResourceRule"]