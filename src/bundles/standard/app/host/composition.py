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

**0.72.3:** each record names the plugin packages it installs (kits, patterns,
providers, runners, storages). The install stroke walks those names.
``INSTALLED_*`` stays the catalog of real packages.

**0.72.4:** each record also names transform rules. The same stroke walks
those names. Service names stay the phenotype field. The host imports that
tuple; ``INSTALLED_SERVICES`` stays the catalog.

History: skeleton 0.50 · living capabilities 0.51 · boot schedule 0.59.2-.4 ·
membership truth 0.59.5 · composition record 0.72.2 · package names 0.72.3 ·
second menus 0.72.4.
Typed name-tuples + saved records — not a manifest DSL.
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

#: Package names each saved record installs (0.72.3).
#: The install stroke walks the record. These tuples are the saved data.
#: ``INSTALLED_*`` in each family package is the catalog of real packages.
RECORD_KITS: tuple[str, ...] = ("present", "authoring")
RECORD_PATTERNS: tuple[str, ...] = ("dag", "parallel", "pipeline", "wizard")
RECORD_PROVIDERS: tuple[str, ...] = ("rest", "palm", "kv", "file", "authoring")
RECORD_RUNNERS: tuple[str, ...] = ("local", "host", "neonroot")
RECORD_STORAGES: tuple[str, ...] = ("memory", "filesystem")
#: Transform rules each saved record installs (0.72.4). Same set on every record.
RECORD_TRANSFORMS: tuple[str, ...] = (
    "rename_field",
    "map_fields",
    "append_item",
    "put_resource",
    "filter_items",
    "count_by",
    "callable",
    "string_format",
    "jsonpath_extract",
    "jsonpath_set",
    "calculate",
    "enrich_resource",
    "date_format",
    "date_parse",
    "lookup",
    "conditional",
    "json_load",
    "json_dump",
    "csv_load",
    "csv_dump",
    "yaml_load",
    "yaml_dump",
    "toml_load",
    "xml_load",
)


@dataclass(frozen=True)
class CompositionRecord:
    """Saved composition data. The host builds a :class:`CompositionProfile` from this."""

    name: str
    services: tuple[str, ...]
    surfaces: tuple[str, ...]
    capabilities: frozenset[str]
    kits: tuple[str, ...]
    patterns: tuple[str, ...]
    providers: tuple[str, ...]
    runners: tuple[str, ...]
    storages: tuple[str, ...]
    transforms: tuple[str, ...]


#: Named shapes. One row is one record. The host does not keep a method per name.
COMPOSITION_RECORDS: tuple[CompositionRecord, ...] = (
    CompositionRecord(
        "all_in_one",
        ALL_SERVICES,
        SERVER_SURFACES,
        DEFAULT_CAPABILITIES,
        RECORD_KITS,
        RECORD_PATTERNS,
        RECORD_PROVIDERS,
        RECORD_RUNNERS,
        RECORD_STORAGES,
        RECORD_TRANSFORMS,
    ),
    CompositionRecord(
        "server",
        ALL_SERVICES,
        SERVER_SURFACES,
        DEFAULT_CAPABILITIES,
        RECORD_KITS,
        RECORD_PATTERNS,
        RECORD_PROVIDERS,
        RECORD_RUNNERS,
        RECORD_STORAGES,
        RECORD_TRANSFORMS,
    ),
    CompositionRecord(
        "embedded",
        CORE_SERVICES,
        (),
        frozenset(),
        RECORD_KITS,
        RECORD_PATTERNS,
        RECORD_PROVIDERS,
        RECORD_RUNNERS,
        RECORD_STORAGES,
        RECORD_TRANSFORMS,
    ),
    CompositionRecord(
        "worker",
        ("execution",),
        (),
        frozenset(),
        RECORD_KITS,
        RECORD_PATTERNS,
        RECORD_PROVIDERS,
        RECORD_RUNNERS,
        RECORD_STORAGES,
        RECORD_TRANSFORMS,
    ),
    CompositionRecord(
        "cli",
        ALL_SERVICES,
        (),
        DEFAULT_CAPABILITIES,
        RECORD_KITS,
        RECORD_PATTERNS,
        RECORD_PROVIDERS,
        RECORD_RUNNERS,
        RECORD_STORAGES,
        RECORD_TRANSFORMS,
    ),
    CompositionRecord(
        "mcp",
        ALL_SERVICES,
        ("mcp",),
        DEFAULT_CAPABILITIES,
        RECORD_KITS,
        RECORD_PATTERNS,
        RECORD_PROVIDERS,
        RECORD_RUNNERS,
        RECORD_STORAGES,
        RECORD_TRANSFORMS,
    ),
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
    """Declared composition: services, surfaces, capabilities, and package names.

    Services, surfaces, and capabilities are the phenotype.
    ``kits`` / ``patterns`` / ``providers`` / ``runners`` / ``storages`` /
    ``transforms`` are the plugin packages and rules this composition installs
    (0.72.3 / 0.72.4).
    """

    services: tuple[str, ...] = ALL_SERVICES
    surfaces: tuple[str, ...] = ()
    capabilities: frozenset[str] = DEFAULT_CAPABILITIES
    kits: tuple[str, ...] = RECORD_KITS
    patterns: tuple[str, ...] = RECORD_PATTERNS
    providers: tuple[str, ...] = RECORD_PROVIDERS
    runners: tuple[str, ...] = RECORD_RUNNERS
    storages: tuple[str, ...] = RECORD_STORAGES
    transforms: tuple[str, ...] = RECORD_TRANSFORMS

    def has(self, capability: str) -> bool:
        """Whether ``capability`` is part of this composition."""
        return capability in self.capabilities

    def exposes(self, surface: str) -> bool:
        """Whether ``surface`` is exposed by this composition."""
        return surface in self.surfaces

    def package_names(self) -> dict[str, tuple[str, ...]]:
        """Plugin package names this composition installs."""
        return {
            "kits": tuple(self.kits),
            "patterns": tuple(self.patterns),
            "providers": tuple(self.providers),
            "runners": tuple(self.runners),
            "storages": tuple(self.storages),
            "transforms": tuple(self.transforms),
        }

    @classmethod
    def from_record(cls, record: CompositionRecord) -> Self:
        """Build a profile from saved composition data."""
        return cls(
            services=tuple(record.services),
            surfaces=tuple(record.surfaces),
            capabilities=frozenset(record.capabilities),
            kits=tuple(record.kits),
            patterns=tuple(record.patterns),
            providers=tuple(record.providers),
            runners=tuple(record.runners),
            storages=tuple(record.storages),
            transforms=tuple(record.transforms),
        )


def composition_profile_from_name(name: str) -> CompositionProfile:
    """Build a :class:`CompositionProfile` from the saved record named ``name``."""
    return CompositionProfile.from_record(composition_record(name))


__all__ = [
    "ALL_SERVICES",
    "COMPOSITION_RECORDS",
    "CORE_SERVICES",
    "DEFAULT_CAPABILITIES",
    "RECORD_KITS",
    "RECORD_PATTERNS",
    "RECORD_PROVIDERS",
    "RECORD_RUNNERS",
    "RECORD_STORAGES",
    "RECORD_TRANSFORMS",
    "SERVER_SURFACES",
    "Capability",
    "CompositionProfile",
    "CompositionRecord",
    "ServiceName",
    "SurfaceName",
    "composition_profile_from_name",
    "composition_record",
]
