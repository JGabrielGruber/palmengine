"""
Host wiring (T2 / 0.48.5, seam 2) — projection read-model construction.

Parameter-based (root-agnostic) so the second composition root (``ServerContext``,
seam 6) can share it. The command/query bus handlers still live in the flat
``app/host/cqrs_wiring.py``; folding that in waits for seam 6, which first breaks
its latent ``ServerContext → services`` import cycle.
"""

from __future__ import annotations

from palm.app.host.wiring.projections import (
    HostProjections,
    build_host_projections,
    register_host_projections,
)

__all__ = [
    "HostProjections",
    "build_host_projections",
    "register_host_projections",
]
