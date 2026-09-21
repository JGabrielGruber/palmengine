"""
CompositionProfile — *what* an app is made of (services, surfaces, capabilities).

The composition axis, twin of ``DeploymentProfile`` (the deployment axis, in
``roles.py``). A running app is assembled from one ``CompositionProfile`` and one
``DeploymentProfile``; the two are orthogonal and never merge.

**0.59.5 / 0.64 / 0.67.7 / 0.67.9 / 0.67.11 / 0.67.13 / 0.67.16 membership:** this profile seeds product
services, surfaces, and capabilities other than ``work_drain``, ``outbox``,
``journal``, ``projections``, ``compensation``, ``webhook``, and ``analytics``. Those names are not composition
members — after structure definition load, install is definition ``capabilities``.
Deployment may feed the settings resolver but does not OR at phase time.
See ADR-028 D4, VISION-0.64, and ``composition_profile_from_settings``.

**0.72.2:** named shapes are saved records (``COMPOSITION_RECORDS``). The host
builds a ``CompositionProfile`` from that data. Preset classmethods are not the path.

History: skeleton 0.50 · living capabilities 0.51 · boot schedule 0.59.2-.4 ·
membership truth 0.59.5 · composition record 0.72.2. Typed name-tuples + saved
records, palm's ``INSTALLED_*`` idiom — not a manifest DSL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Self

ServiceName = Literal[
    "inspect",
    "session",
    "definitions",
    "execution",
    "assist",
    "design",
    "analytics",
]
SurfaceName = Literal["rest", "websocket", "mcp", "explorer", "studio"]
Capability = Literal[
    "workloads",  # 0.56 — WorkloadEngine plane (host OFF by default)
]

#: The full service set the host builds today (pinned to CORE_SERVICE_PROVIDERS by tests).
ALL_SERVICES: tuple[ServiceName, ...] = (
    "inspect",
    "session",
    "definitions",
    "execution",
    "assist",
    "design",
    "analytics",
)
#: Minimal services for an embedded/library shape — no assist/design/analytics chrome.
#: Includes product ``session`` (0.58.12) so core submit paths have the surface door.
CORE_SERVICES: tuple[ServiceName, ...] = (
    "inspect",
    "session",
    "definitions",
    "execution",
)
#: The surfaces the server runtime ships (see runtimes/server/surfaces default_surfaces).
SERVER_SURFACES: tuple[SurfaceName, ...] = ("rest", "websocket", "mcp", "explorer", "studio")
#: Background/optional capabilities on for a full host by default.
DEFAULT_CAPABILITIES: frozenset[Capability] = frozenset(
    {
        "workloads",
    }
)


@dataclass(frozen=True)
class CompositionRecord:
    """Saved composition data. The host builds a :class:`CompositionProfile` from this."""

    name: str
    services: tuple[str, ...]
    surfaces: tuple[str, ...]
    capabilities: frozenset[str]


#: Named shapes. One row is one record. The host does not keep a method per name.
COMPOSITION_RECORDS: tuple[CompositionRecord, ...] = (
    CompositionRecord(
        "all_in_one",
        ALL_SERVICES,
        SERVER_SURFACES,
        DEFAULT_CAPABILITIES,
    ),
    CompositionRecord(
        "server",
        ALL_SERVICES,
        SERVER_SURFACES,
        DEFAULT_CAPABILITIES,
    ),
    CompositionRecord("embedded", CORE_SERVICES, (), frozenset()),
    CompositionRecord("worker", ("execution",), (), frozenset()),
    CompositionRecord("cli", ALL_SERVICES, (), DEFAULT_CAPABILITIES),
    CompositionRecord("mcp", ALL_SERVICES, ("mcp",), DEFAULT_CAPABILITIES),
)

_RECORDS_BY_NAME: dict[str, CompositionRecord] = {row.name: row for row in COMPOSITION_RECORDS}


def composition_record(name: str) -> CompositionRecord:
    """Return the saved composition record for ``name``."""
    key = str(name).strip().lower()
    try:
        return _RECORDS_BY_NAME[key]
    except KeyError as exc:
        known = ", ".join(row.name for row in COMPOSITION_RECORDS)
        raise ValueError(f"Unknown composition record {name!r}; expected one of {known}") from exc


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

    @classmethod
    def from_record(cls, record: CompositionRecord) -> Self:
        """Build a profile from saved composition data."""
        return cls(
            services=tuple(record.services),
            surfaces=tuple(record.surfaces),
            capabilities=frozenset(record.capabilities),
        )


def composition_profile_from_name(name: str) -> CompositionProfile:
    """Build a :class:`CompositionProfile` from the saved record named ``name``."""
    return CompositionProfile.from_record(composition_record(name))


__all__ = [
    "ALL_SERVICES",
    "COMPOSITION_RECORDS",
    "CORE_SERVICES",
    "DEFAULT_CAPABILITIES",
    "SERVER_SURFACES",
    "Capability",
    "CompositionProfile",
    "CompositionRecord",
    "ServiceName",
    "SurfaceName",
    "composition_profile_from_name",
    "composition_record",
]
