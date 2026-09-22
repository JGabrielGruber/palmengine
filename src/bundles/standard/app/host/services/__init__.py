"""
Host service construction (T2 / 0.48.2).

A typed, dependency-ordered registry that builds the host's core services out of
``ApplicationHost._wire_cqrs``. See docs/adr/018-application-host-decomposition.md.

Post-build product identity (assist↔analytics, dashboards, service CQRS) lives in
:mod:`palm.app.host.services.packaging` — shared with host-less ``ServerContext``.
"""

from __future__ import annotations

from bundles.standard.app.host.services.packaging import (
    ProductServiceBag,
    apply_product_packaging,
    bag_from_built,
)
from bundles.standard.app.host.services.providers import CORE_SERVICE_PROVIDERS, core_service_registry
from bundles.standard.app.host.services.registry import (
    HostServiceContext,
    HostServiceRegistry,
    ServiceProvider,
)

__all__ = [
    "CORE_SERVICE_PROVIDERS",
    "HostServiceContext",
    "HostServiceRegistry",
    "ProductServiceBag",
    "ServiceProvider",
    "apply_product_packaging",
    "bag_from_built",
    "core_service_registry",
]
