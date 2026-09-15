"""
Vitality schema constants — versioned seat-report contract (0.61.1).

Stable names for kinds, states, lineage, and the schema id. Growth adds
fields behind a new schema version; do not silently reshape ``/1``.
"""

from __future__ import annotations

from typing import Final, Literal

# ── Schema ───────────────────────────────────────────────────────────────────

SEAT_REPORT_SCHEMA: Final[str] = "palm.seat_report/1"
"""Versioned seat-report document id. Bump only with intentional migration."""

# ── Kind ─────────────────────────────────────────────────────────────────────

SeatKindName = Literal[
    "plane",
    "supervisor",
    "supervisor_service",
    "port",
    "log",
    "boot",
    "engine",
    "other",
]

KIND_PLANE: Final[str] = "plane"
KIND_SUPERVISOR: Final[str] = "supervisor"
KIND_SUPERVISOR_SERVICE: Final[str] = "supervisor_service"
KIND_PORT: Final[str] = "port"
KIND_LOG: Final[str] = "log"
KIND_BOOT: Final[str] = "boot"
KIND_ENGINE: Final[str] = "engine"
KIND_OTHER: Final[str] = "other"

KNOWN_KINDS: Final[frozenset[str]] = frozenset(
    {
        KIND_PLANE,
        KIND_SUPERVISOR,
        KIND_SUPERVISOR_SERVICE,
        KIND_PORT,
        KIND_LOG,
        KIND_BOOT,
        KIND_ENGINE,
        KIND_OTHER,
    }
)

# ── State ────────────────────────────────────────────────────────────────────

SeatStateName = Literal["ok", "degraded", "absent", "error", "skipped"]

STATE_OK: Final[str] = "ok"
STATE_DEGRADED: Final[str] = "degraded"
STATE_ABSENT: Final[str] = "absent"
STATE_ERROR: Final[str] = "error"
STATE_SKIPPED: Final[str] = "skipped"

KNOWN_STATES: Final[frozenset[str]] = frozenset(
    {
        STATE_OK,
        STATE_DEGRADED,
        STATE_ABSENT,
        STATE_ERROR,
        STATE_SKIPPED,
    }
)

# ── Lineage ──────────────────────────────────────────────────────────────────

SeatLineageName = Literal["native", "sampled"]

LINEAGE_NATIVE: Final[str] = "native"
"""Seat implemented ``seat_report()`` in its own vocabulary (rare)."""

LINEAGE_SAMPLED: Final[str] = "sampled"
"""Eyes read public seat API and stash **raw** under ``meta.raw``; product presents."""

# Deprecated read residue (CS-007 paid): old snapshots may still say "adapter".
# Coerce to sampled on load; do not emit new adapter reports.
LINEAGE_ADAPTER: Final[str] = "adapter"

KNOWN_LINEAGES: Final[frozenset[str]] = frozenset(
    {LINEAGE_NATIVE, LINEAGE_SAMPLED}
)
LEGACY_LINEAGES: Final[frozenset[str]] = frozenset({LINEAGE_ADAPTER})

# ── Well-known seat ids (discovery seeds — not a closed forever menu) ───────
# New seats appear by attachment + probe registration. These ids stay stable
# for the seeds Palm attaches after system start (0.57–0.60 living graph).

# Planes hub + member seat ids (members expanded from live SystemPlanes).
SEAT_PLANES: Final[str] = "planes"
SEAT_WAIT_PLANE: Final[str] = "wait_plane"
SEAT_SESSION_PLANE: Final[str] = "session_plane"
SEAT_WORK_PLANE: Final[str] = "work_plane"
SEAT_SUPERVISOR: Final[str] = "supervisor"
SEAT_EXECUTION: Final[str] = "execution"
SEAT_INSTALL: Final[str] = "install"
"""InstallInterface collaborator board (peer of execution)."""
SEAT_STRUCTURE: Final[str] = "structure"
"""Structure seat — definition + admission gate (0.63)."""
SEAT_SYSTEM_LOG: Final[str] = "system_log"
SEAT_BOOT_MEMBERSHIP: Final[str] = "boot_membership"

# Supervisor service seats use: supervisor.<service_name>
SUPERVISOR_SERVICE_PREFIX: Final[str] = "supervisor."

# ── Walk options / capability seed (registry body lands 0.61.2) ─────────────

# ── Snapshot / capability ids (0.61.2+) ──────────────────────────────────────

VITALITY_SNAPSHOT_SCHEMA: Final[str] = "palm.vitality_snapshot/1"
"""Versioned projection snapshot document id."""

CAPABILITY_FRAGMENT_SCHEMA: Final[str] = "palm.vitality_fragment/1"
"""Versioned capability fragment document id."""

CAPABILITY_SEAT_WALK: Final[str] = "seat_walk"
"""Core observe: discover seats + fold seat reports (landed 0.61.1/0.61.2)."""

CAPABILITY_EMISSION_WINDOW: Final[str] = "emission_window"
"""Observe: recent emissions + actor partition (0.61.3 body)."""

# ── Emission identity (ADR-030 D8) ───────────────────────────────────────────

ACTOR_KIND_HUMAN: Final[str] = "human"
ACTOR_KIND_AGENT: Final[str] = "agent"
ACTOR_KIND_PROBE: Final[str] = "probe"
ACTOR_KIND_SYSTEM: Final[str] = "system"
ACTOR_KIND_PEER: Final[str] = "peer"
ACTOR_KIND_UNKNOWN: Final[str] = "unknown"

KNOWN_ACTOR_KINDS: Final[frozenset[str]] = frozenset(
    {
        ACTOR_KIND_HUMAN,
        ACTOR_KIND_AGENT,
        ACTOR_KIND_PROBE,
        ACTOR_KIND_SYSTEM,
        ACTOR_KIND_PEER,
        ACTOR_KIND_UNKNOWN,
    }
)

CHANNEL_SYSTEM_LOG: Final[str] = "system_log"
CHANNEL_WORK_PLANE: Final[str] = "work_plane"

DEFAULT_EMISSION_WINDOW_LIMIT: Final[int] = 40
"""Default max system-log records folded into one emission_window sample."""

CAPABILITY_PROCESS_RESOURCES: Final[str] = "process_resources"
"""Optional observe: RSS/CPU/threads (stdlib; installed 0.61.8)."""

CAPABILITY_LOADED_BULK: Final[str] = "loaded_bulk"
"""Optional observe: light size of attached seats (installed 0.61.9)."""

CAPABILITY_BENCHMARK: Final[str] = "benchmark"
"""Active tool: recipe + observe snapshot diff (installed 0.61.10; off by default)."""

CAPABILITY_MONITOR_AGENT: Final[str] = "monitor_agent"
"""Active tool (intention until ready)."""

# Maturity / role for registry growth
MATURITY_INSTALLED: Final[str] = "installed"
MATURITY_INTENTION: Final[str] = "intention"

ROLE_OBSERVE: Final[str] = "observe"
ROLE_TOOL: Final[str] = "tool"

COST_CHEAP: Final[str] = "cheap"
COST_MODERATE: Final[str] = "moderate"
COST_EXPENSIVE: Final[str] = "expensive"


def supervisor_service_seat_id(service_name: str) -> str:
    """Stable seat id for one supervised continuous service."""
    name = str(service_name or "").strip()
    if not name:
        raise ValueError("supervisor service name required")
    if name.startswith(SUPERVISOR_SERVICE_PREFIX):
        return name
    return f"{SUPERVISOR_SERVICE_PREFIX}{name}"


__all__ = [
    "ACTOR_KIND_AGENT",
    "ACTOR_KIND_HUMAN",
    "ACTOR_KIND_PEER",
    "ACTOR_KIND_PROBE",
    "ACTOR_KIND_SYSTEM",
    "ACTOR_KIND_UNKNOWN",
    "CAPABILITY_BENCHMARK",
    "CAPABILITY_EMISSION_WINDOW",
    "CAPABILITY_FRAGMENT_SCHEMA",
    "CAPABILITY_LOADED_BULK",
    "CAPABILITY_MONITOR_AGENT",
    "CAPABILITY_PROCESS_RESOURCES",
    "CAPABILITY_SEAT_WALK",
    "CHANNEL_SYSTEM_LOG",
    "CHANNEL_WORK_PLANE",
    "COST_CHEAP",
    "COST_EXPENSIVE",
    "COST_MODERATE",
    "DEFAULT_EMISSION_WINDOW_LIMIT",
    "KIND_BOOT",
    "KNOWN_ACTOR_KINDS",
    "KIND_ENGINE",
    "KIND_LOG",
    "KIND_OTHER",
    "KIND_PLANE",
    "KIND_PORT",
    "KIND_SUPERVISOR",
    "KIND_SUPERVISOR_SERVICE",
    "KNOWN_KINDS",
    "KNOWN_LINEAGES",
    "KNOWN_STATES",
    "LEGACY_LINEAGES",
    "LINEAGE_ADAPTER",
    "LINEAGE_NATIVE",
    "LINEAGE_SAMPLED",
    "MATURITY_INSTALLED",
    "MATURITY_INTENTION",
    "ROLE_OBSERVE",
    "ROLE_TOOL",
    "SEAT_STRUCTURE",
    "SEAT_BOOT_MEMBERSHIP",
    "SEAT_EXECUTION",
    "SEAT_INSTALL",
    "SEAT_PLANES",
    "SEAT_REPORT_SCHEMA",
    "SEAT_SESSION_PLANE",
    "SEAT_SUPERVISOR",
    "SEAT_SYSTEM_LOG",
    "SEAT_WAIT_PLANE",
    "SEAT_WORK_PLANE",
    "STATE_ABSENT",
    "STATE_DEGRADED",
    "STATE_ERROR",
    "STATE_OK",
    "STATE_SKIPPED",
    "SUPERVISOR_SERVICE_PREFIX",
    "SeatKindName",
    "SeatLineageName",
    "SeatStateName",
    "VITALITY_SNAPSHOT_SCHEMA",
    "supervisor_service_seat_id",
]
