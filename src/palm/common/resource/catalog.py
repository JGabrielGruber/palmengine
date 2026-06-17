"""Resource catalog — discovery and rich metadata for definitions and providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.core.registry import provider_registry
from palm.definitions.resource import ResourceDefinition

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository


@dataclass(frozen=True)
class ResourceCatalogEntry:
    """Enriched resource row for doctor, Explorer, and tooling."""

    definition_id: str
    name: str
    provider: str
    action: str
    resource_id: str | None
    param_keys: tuple[str, ...]
    has_input_schema: bool
    has_output_schema: bool
    provider_description: str
    provider_actions: tuple[str, ...]

    def summary(self) -> str:
        parts: list[str] = []
        if self.resource_id:
            parts.append(self.resource_id)
        if self.param_keys:
            parts.append(f"{len(self.param_keys)} param(s)")
        if self.has_input_schema or self.has_output_schema:
            bits: list[str] = []
            if self.has_input_schema:
                bits.append("in")
            if self.has_output_schema:
                bits.append("out")
            parts.append(f"schema:{'+'.join(bits)}")
        if self.provider_actions:
            parts.append(f"provider actions: {', '.join(self.provider_actions)}")
        return ", ".join(parts) if parts else "—"


class ResourceCatalog:
    """Discover resource definitions with provider capability metadata."""

    def __init__(self, repository: DefinitionRepository) -> None:
        self._repository = repository

    def entries(self) -> list[ResourceCatalogEntry]:
        """Return all catalog entries sorted by name."""
        items = [self._entry_for(resource) for resource in self._repository.list_resources()]
        return sorted(items, key=lambda item: item.name)

    def by_provider(self, provider: str) -> list[ResourceCatalogEntry]:
        return [entry for entry in self.entries() if entry.provider == provider]

    def describe(self, ref: str, *, by_id: bool = False) -> dict[str, Any]:
        """Return a structured description for CLI, doctor, or Explorer detail views."""
        resource = self._repository.get_resource(ref, by_id=by_id)
        entry = self._entry_for(resource)
        return {
            "definition_id": entry.definition_id,
            "name": entry.name,
            "provider": entry.provider,
            "action": entry.action,
            "resource_id": entry.resource_id,
            "params": dict(resource.params),
            "param_keys": list(entry.param_keys),
            "input_schema": resource.input_schema,
            "output_schema": resource.output_schema,
            "output_key": resource.output_key,
            "metadata": dict(resource.metadata),
            "provider_description": entry.provider_description,
            "provider_actions": list(entry.provider_actions),
            "summary": entry.summary(),
        }

    def _entry_for(self, resource: ResourceDefinition) -> ResourceCatalogEntry:
        provider_description = ""
        provider_actions: tuple[str, ...] = ()
        try:
            cls = provider_registry.get(resource.provider)
            probe = cls(name=resource.provider)
            descriptor = probe.describe()
            provider_description = descriptor.description
            provider_actions = tuple(action.name for action in descriptor.actions)
        except Exception:
            provider_description = f"{resource.provider} provider"
        return ResourceCatalogEntry(
            definition_id=resource.definition_id,
            name=resource.name,
            provider=resource.provider,
            action=resource.action,
            resource_id=resource.resource_id,
            param_keys=tuple(sorted(resource.params)),
            has_input_schema=resource.has_input_schema,
            has_output_schema=resource.has_output_schema,
            provider_description=provider_description,
            provider_actions=provider_actions,
        )
