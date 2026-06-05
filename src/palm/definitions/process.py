"""
Process definition — long-running or scheduled work unit.

Processes compose flows with storage and provider bindings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.definitions.flow import FlowDefinition


@dataclass
class ProcessDefinition:
    """Named process referencing one or more flows."""

    name: str
    flows: list[FlowDefinition] = field(default_factory=list)
    storage: str = "memory"
    metadata: dict[str, Any] = field(default_factory=dict)
