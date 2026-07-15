"""Studio data fetching — registry-driven palette aggregation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.query import ListFlowsQuery
from palm.common.transforms.catalog import transform_description
from palm.core.registry import pattern_registry
from palm.core.transform.base import TransformMode
from palm.core.transform.registry import transform_registry

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext


class StudioFetcher:
    """Thin facade for Palm Studio palette and catalog reads."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    @property
    def version(self) -> str:
        return self._ctx.runtime.version

    def list_patterns(self) -> list[dict[str, str]]:
        import palm.patterns  # noqa: F401 — register installed patterns

        items: list[dict[str, str]] = []
        for name in pattern_registry.names():
            cls = pattern_registry.get(name)
            doc = (cls.__doc__ or "").strip().split("\n")[0]
            items.append({"name": name, "class": cls.__name__, "summary": doc})
        return items

    def list_transforms(self) -> list[dict[str, str]]:
        from palm.common.transforms import autoload

        autoload()
        items: list[dict[str, str]] = []
        for name in transform_registry.names():
            rule_cls = transform_registry.get(name)
            mode = getattr(rule_cls, "mode", TransformMode.SINGLE)
            items.append(
                {
                    "name": name,
                    "description": transform_description(name),
                    "mode": str(mode.value if hasattr(mode, "value") else mode),
                }
            )
        return items

    def list_resources(self) -> list[dict[str, Any]]:
        from palm.common.resource.catalog import ResourceCatalog

        entries = ResourceCatalog(self._ctx.runtime.repository).entries()
        return [
            {
                "definition_id": entry.definition_id,
                "name": entry.name,
                "provider": entry.provider,
                "action": entry.action,
                "resource_id": entry.resource_id,
                "param_keys": list(entry.param_keys),
                "has_input_schema": entry.has_input_schema,
                "has_output_schema": entry.has_output_schema,
                "provider_actions": list(entry.provider_actions),
                "summary": entry.summary(),
            }
            for entry in entries
        ]

    def list_flow_templates(self) -> list[dict[str, Any]]:
        flows = self._ctx.ask(ListFlowsQuery())
        return [
            {
                "flow_id": flow.definition_id,
                "name": flow.name,
                "pattern": flow.pattern,
                "has_state_schema": flow.has_state_schema,
            }
            for flow in flows
        ]
