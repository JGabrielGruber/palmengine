"""
Host work plane (T2 / 0.48.3) — WorkIntent drain + inbound resource bindings.

The deferred-work / inbound-binding services the host wires during ``start``.
Seam 4's ``WorkPlaneCoordinator`` (0.48.3b) will own their wiring and lifecycle;
for now this package groups the services out of the flat ``app/host`` directory.
"""

from __future__ import annotations

from palm.app.host.workplane.coordinator import WorkPlaneCoordinator
from palm.app.host.workplane.inbound_service import InboundBinding, InboundBindingService
from palm.app.host.workplane.work_drain_service import WorkDrainService

__all__ = [
    "InboundBinding",
    "InboundBindingService",
    "WorkDrainService",
    "WorkPlaneCoordinator",
]
