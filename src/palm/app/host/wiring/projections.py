"""
Projection wiring (T2 / 0.48.5, seam 2) — build + register the host's read models.

Parameter-based (root-agnostic): takes storage / instance-manager / projection
manager, not a host — so the second composition root (``ServerContext``, seam 6)
can share it. Extracted verbatim from ``ApplicationHost._wire_cqrs``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.common.cqrs.projection import ProjectionManager
from palm.common.cqrs.projections.instance_index import InstanceIndexProjection
from palm.common.cqrs.projections.job_status_board import JobStatusBoardProjection
from palm.common.cqrs.projections.resource_invocation import ResourceInvocationProjection
from palm.common.patterns._registry import get_projection_factory, registered_projection_factories


@dataclass
class HostProjections:
    """The read-model projections a host builds and serves queries from."""

    instance: InstanceIndexProjection
    resource: ResourceInvocationProjection
    job_board: JobStatusBoardProjection
    patterns: dict[str, Any] = field(default_factory=dict)


def build_host_projections(storage: Any, instance_manager: Any) -> HostProjections:
    """Construct the core + pattern projections over ``storage``."""
    import palm.patterns  # noqa: F401 — ensure pattern projection factories are registered

    patterns: dict[str, Any] = {}
    for pattern_name in registered_projection_factories():
        factory = get_projection_factory(pattern_name)
        if factory is not None:
            patterns[pattern_name] = factory(storage)
    return HostProjections(
        instance=InstanceIndexProjection(storage, instance_manager),
        resource=ResourceInvocationProjection(storage),
        job_board=JobStatusBoardProjection(storage),
        patterns=patterns,
    )


def register_host_projections(manager: ProjectionManager, projections: HostProjections) -> None:
    """Register the projections into ``manager`` (order matches legacy wiring)."""
    manager.register(projections.instance)
    for projection in projections.patterns.values():
        manager.register(projection)
    manager.register(projections.resource)
    manager.register(projections.job_board)


__all__ = [
    "HostProjections",
    "build_host_projections",
    "register_host_projections",
]
