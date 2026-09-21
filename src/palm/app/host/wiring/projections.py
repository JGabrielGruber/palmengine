"""Pattern projection extras for host query wire.

Core read models live on the install board (DNA hand). This module only
builds pattern extras registered onto that same manager.
"""

from __future__ import annotations

from typing import Any

from palm.common.patterns._registry import get_projection_factory, registered_projection_factories


def build_pattern_projections(storage: Any) -> dict[str, Any]:
    """Construct pattern extras. Core read models live on the install board.

    Pattern packages are already installed by the composition stroke.
    """
    patterns: dict[str, Any] = {}
    for pattern_name in registered_projection_factories():
        factory = get_projection_factory(pattern_name)
        if factory is not None:
            patterns[pattern_name] = factory(storage)
    return patterns


__all__ = [
    "build_pattern_projections",
]
