"""
Process definition — long-running or scheduled work unit.

Processes compose flows with storage and provider bindings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.definitions.flow import FlowDefinition

_DEFINITION_VERSION = 1


@dataclass
class ProcessDefinition:
    """Named process referencing one or more flows."""

    name: str
    flows: list[FlowDefinition] = field(default_factory=list)
    storage: str = "memory"
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ProcessDefinition name must be non-empty")

    @property
    def definition_id(self) -> str:
        """Stable identifier used for storage keys (defaults to ``name``)."""
        return self.id if self.id else self.name

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dict for persistence."""
        payload: dict[str, Any] = {
            "version": _DEFINITION_VERSION,
            "kind": "process",
            "name": self.name,
            "storage": self.storage,
            "metadata": dict(self.metadata),
            "flows": [flow.to_dict() for flow in self.flows],
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessDefinition:
        """Restore a process definition from ``to_dict`` output or legacy shape."""
        raw_flows = data.get("flows") or []
        flows = [
            FlowDefinition.from_dict(item) if isinstance(item, dict) else item for item in raw_flows
        ]
        if flows and not all(isinstance(f, FlowDefinition) for f in flows):
            raise TypeError("Process flows must be FlowDefinition or dict payloads")

        return cls(
            name=str(data["name"]),
            flows=flows,
            storage=str(data.get("storage", "memory")),
            metadata=dict(data.get("metadata") or {}),
            id=data.get("id"),
        )

    def catalog_summary(self) -> dict[str, Any]:
        """Minimal catalog list row — facts only, no transport or agent hints."""
        summary: dict[str, Any] = {
            "process_id": self.definition_id,
            "name": self.name,
            "storage": self.storage,
            "flow_count": len(self.flows),
        }
        metadata = self.metadata or {}
        entry_flow = metadata.get("entry_flow")
        if isinstance(entry_flow, str) and entry_flow:
            summary["entry_flow"] = entry_flow
        return summary

    def to_storage_record(self) -> dict[str, Any]:
        """Envelope stored under the repository storage key."""
        return self.to_dict()
