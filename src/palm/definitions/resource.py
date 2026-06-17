"""
Resource definition — declarative description of an external capability invocation.

Resources reference registered providers and bind parameters for later resolution
by :class:`~palm.core.resource.ResourceEngine`. Phase 1 catalogs definitions;
Phase 2 adds ``invoke()`` with param binding and provider ``ProviderResult``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_DEFINITION_VERSION = 1


@dataclass
class ResourceDefinition:
    """Named resource contract: provider, action, identifiers, and schemas."""

    name: str
    provider: str
    id: str | None = None
    action: str = "fetch"
    resource_id: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    output_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ResourceDefinition name must be non-empty")
        if not self.provider:
            raise ValueError("ResourceDefinition provider must be non-empty")
        if not self.action:
            raise ValueError("ResourceDefinition action must be non-empty")

    @property
    def definition_id(self) -> str:
        """Stable identifier used for storage keys (defaults to ``name``)."""
        return self.id if self.id else self.name

    @property
    def has_input_schema(self) -> bool:
        """Return whether an input validation schema is configured."""
        return self.input_schema is not None

    @property
    def has_output_schema(self) -> bool:
        """Return whether an output validation schema is configured."""
        return self.output_schema is not None

    @property
    def has_schemas(self) -> bool:
        """Return whether any input or output schema is configured."""
        return self.has_input_schema or self.has_output_schema

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dict for persistence."""
        payload: dict[str, Any] = {
            "version": _DEFINITION_VERSION,
            "kind": "resource",
            "name": self.name,
            "provider": self.provider,
            "action": self.action,
            "params": dict(self.params),
            "metadata": dict(self.metadata),
        }
        if self.id is not None:
            payload["id"] = self.id
        if self.resource_id is not None:
            payload["resource_id"] = self.resource_id
        if self.input_schema is not None:
            payload["input_schema"] = dict(self.input_schema)
        if self.output_schema is not None:
            payload["output_schema"] = dict(self.output_schema)
        if self.output_key is not None:
            payload["output_key"] = self.output_key
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceDefinition:
        """Restore a resource definition from ``to_dict`` output or legacy shape."""
        inline_input = data.get("input_schema")
        input_schema = dict(inline_input) if isinstance(inline_input, dict) else None
        inline_output = data.get("output_schema")
        output_schema = dict(inline_output) if isinstance(inline_output, dict) else None
        resource_id = data.get("resource_id")
        output_key = data.get("output_key")
        return cls(
            name=str(data["name"]),
            provider=str(data["provider"]),
            id=data.get("id"),
            action=str(data.get("action", "fetch")),
            resource_id=str(resource_id) if resource_id is not None else None,
            params=dict(data.get("params") or {}),
            input_schema=input_schema,
            output_schema=output_schema,
            output_key=str(output_key) if output_key is not None else None,
            metadata=dict(data.get("metadata") or {}),
        )

    def to_storage_record(self) -> dict[str, Any]:
        """Envelope stored under the repository storage key."""
        return self.to_dict()