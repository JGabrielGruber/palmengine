"""
Host service construction (T2 / 0.48.2).

A typed, dependency-ordered registry that builds the host's core services out of
``ApplicationHost._wire_cqrs``. See docs/adr/018-application-host-decomposition.md.
"""

from __future__ import annotations

from palm.app.host.services.providers import CORE_SERVICE_PROVIDERS, core_service_registry
from palm.app.host.services.registry import (
    HostServiceContext,
    HostServiceRegistry,
    ServiceProvider,
)

__all__ = [
    "CORE_SERVICE_PROVIDERS",
    "HostServiceContext",
    "HostServiceRegistry",
    "ServiceProvider",
    "core_service_registry",
]
