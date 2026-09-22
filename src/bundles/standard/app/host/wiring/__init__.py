"""
Host wiring (T2 / 0.48.6, seam 2) — projections + command/query bus handlers.

Parameter-based (root-agnostic) so the second composition root (``ServerContext``)
can share it. Folded in 0.48.6 once the latent ``ServerContext → services`` cycle
was broken (via lazy ``common.runtimes.server`` composition-root exports).
"""

from __future__ import annotations

from bundles.standard.app.host.wiring.cqrs import (
    collect_cqrs_command_types,
    collect_cqrs_query_types,
    wire_command_bus,
    wire_query_bus,
)
from bundles.standard.app.host.wiring.projections import (
    build_pattern_projections,
)

__all__ = [
    "build_pattern_projections",
    "collect_cqrs_command_types",
    "collect_cqrs_query_types",
    "wire_command_bus",
    "wire_query_bus",
]
