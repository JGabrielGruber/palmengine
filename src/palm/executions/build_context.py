"""
Build context — dependencies passed when materializing patterns from definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.core.event import EventEngine
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.commit import CommitRegistry, default_commit_registry
from palm.patterns.wizard.validation import ValidationRegistry, default_validation_registry


@dataclass
class PatternBuildContext:
    """Runtime services used when constructing executable patterns."""

    event_engine: EventEngine | None = None
    resource_engine: ResourceEngine | None = None
    commit_registry: CommitRegistry | None = None
    validation_registry: ValidationRegistry | None = None
    wizard_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def resolved_commit_registry(self) -> CommitRegistry:
        return self.commit_registry or default_commit_registry()

    @property
    def resolved_validation_registry(self) -> ValidationRegistry:
        return self.validation_registry or default_validation_registry()