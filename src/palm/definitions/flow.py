"""
Flow definition — declarative description of a runnable flow.

Flows reference registered patterns and bind runtime configuration. Full YAML/JSON
loading will be added in a later iteration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FlowDefinition:
    """Named flow with pattern binding and optional metadata."""

    name: str
    pattern: str
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "pattern": self.pattern, "options": self.options}
