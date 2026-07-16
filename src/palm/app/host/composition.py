"""
CompositionProfile — *what* an app is made of (services, surfaces, capabilities).

The composition axis, twin of ``DeploymentProfile`` (the deployment axis, in
``roles.py``). A running app is assembled from one ``CompositionProfile`` and one
``DeploymentProfile``; the two are orthogonal and never merge.

0.50.1 is the **skeleton**: the profile is *declared* and its ``all_in_one`` preset
is pinned against what ``ApplicationHost`` builds today (see
``tests/test_composition_profile_0_50.py``). It is not yet wired — later slices make
the host assemble from it (0.50.2), drive surfaces from it (0.50.3), and dissolve
``ServerContext`` into ``CompositionProfile.server()`` (0.50.5). See VISION-0.50 / ADR-019.

The design mirrors ``DeploymentProfile``: a typed dataclass of name-tuples + presets,
reusing palm's own ``INSTALLED_*`` idiom rather than a manifest DSL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Self

ServiceName = Literal["system", "definitions", "execution", "assist", "design", "analytics"]
SurfaceName = Literal["rest", "websocket", "mcp", "explorer", "studio"]
Capability = Literal["work_drain", "outbox", "compensation", "webhook", "journal", "analytics"]

#: The full service set the host builds today (pinned to CORE_SERVICE_PROVIDERS by tests).
ALL_SERVICES: tuple[ServiceName, ...] = (
    "system",
    "definitions",
    "execution",
    "assist",
    "design",
    "analytics",
)
#: Minimal services for an embedded/library shape — no assist/design/analytics chrome.
CORE_SERVICES: tuple[ServiceName, ...] = ("system", "definitions", "execution")
#: The surfaces the server runtime ships (see runtimes/server/surfaces default_surfaces).
SERVER_SURFACES: tuple[SurfaceName, ...] = ("rest", "websocket", "mcp", "explorer", "studio")
#: Background/optional capabilities on for a full host by default.
DEFAULT_CAPABILITIES: frozenset[Capability] = frozenset({"outbox", "compensation", "journal", "analytics"})


@dataclass(frozen=True)
class CompositionProfile:
    """The declared composition of an app: which services, surfaces, and capabilities."""

    services: tuple[str, ...] = ALL_SERVICES
    surfaces: tuple[str, ...] = ()
    capabilities: frozenset[str] = DEFAULT_CAPABILITIES

    def has(self, capability: str) -> bool:
        """Whether ``capability`` is part of this composition."""
        return capability in self.capabilities

    def exposes(self, surface: str) -> bool:
        """Whether ``surface`` is exposed by this composition."""
        return surface in self.surfaces

    # ── Presets — palm's already-shipped shapes, declared ────────────────────

    @classmethod
    def all_in_one(cls) -> Self:
        """The full host — every service + every surface available, background work on.

        Surfaces are *available*; the server deployment mounts them, other deployments
        (CLI) simply don't run a server. So all_in_one declares the full surface set to
        stay behavior-preserving when server-deployed (the common case)."""
        return cls(
            services=ALL_SERVICES,
            surfaces=SERVER_SURFACES,
            capabilities=DEFAULT_CAPABILITIES | {"work_drain"},
        )

    @classmethod
    def server(cls) -> Self:
        """The HTTP server shape — every service + all surfaces + webhook dispatch."""
        return cls(
            services=ALL_SERVICES,
            surfaces=SERVER_SURFACES,
            capabilities=DEFAULT_CAPABILITIES | {"work_drain", "webhook"},
        )

    @classmethod
    def embedded(cls) -> Self:
        """Library / embedded (the palmengine-django case) — core services, no surfaces,
        no background services. Just submit / ask."""
        return cls(services=CORE_SERVICES, surfaces=(), capabilities=frozenset())

    @classmethod
    def worker(cls) -> Self:
        """Headless worker/daemon — execution + deferred-work drain, no surfaces."""
        return cls(
            services=("execution",),
            surfaces=(),
            capabilities=frozenset({"work_drain", "outbox"}),
        )

    @classmethod
    def cli(cls) -> Self:
        """The CLI/REPL shape — full services, no server surfaces."""
        return cls(
            services=ALL_SERVICES,
            surfaces=(),
            capabilities=DEFAULT_CAPABILITIES | {"work_drain"},
        )

    @classmethod
    def mcp(cls) -> Self:
        """The MCP operator shape — full services, MCP surface only."""
        return cls(services=ALL_SERVICES, surfaces=("mcp",), capabilities=DEFAULT_CAPABILITIES)


__all__ = [
    "ALL_SERVICES",
    "CORE_SERVICES",
    "DEFAULT_CAPABILITIES",
    "SERVER_SURFACES",
    "Capability",
    "CompositionProfile",
    "ServiceName",
    "SurfaceName",
]
