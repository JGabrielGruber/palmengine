"""
Build context — dependencies passed when materializing patterns from definitions.

Pattern-specific defaults (e.g. wizard commit registries) are resolved inside
each ``palm.patterns.<name>`` builder, not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.core.event import EventEngine
from palm.core.resource import ResourceEngine


@dataclass
class PatternBuildContext:
    """Runtime services used when constructing executable patterns."""

    event_engine: EventEngine | None = None
    resource_engine: ResourceEngine | None = None
    commit_registry: Any | None = None