"""
Locked boot phase tables (0.59.2).

Phase ids are the schedule contract. Handlers migrate into seats over later
slices; until then most seats are ``imperative`` (code still in start soup)
or ``stub`` (named only). Observation uses the same ids via SystemLog.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ScheduleName = Literal["host", "system"]
PhaseSeat = Literal[
    "implemented",  # walker (or early seat) owns a real body
    "imperative",  # still runs in ApplicationHost / BaseRuntime.start soup
    "stub",  # named seat; body not migrated
]


@dataclass(frozen=True)
class PhaseSpec:
    """One seat on a boot schedule."""

    id: str
    schedule: ScheduleName
    seat: PhaseSeat
    description: str = ""
    optional: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "schedule": self.schedule,
            "seat": self.seat,
            "description": self.description,
            "optional": self.optional,
        }


# ── Host schedule (ApplicationHost) ─────────────────────────────────────────
# 0.59.4 — full table walked by ApplicationHost.start (all seats implemented).

HOST_PHASES: tuple[PhaseSpec, ...] = (
    PhaseSpec(
        "host.system_log",
        "host",
        "implemented",
        "Early console / ring — configure SystemLog from boot mode",
    ),
    PhaseSpec(
        "host.kernel.bootstrap",
        "host",
        "implemented",
        "PalmKernel.bootstrap → ensure plugins",
    ),
    PhaseSpec(
        "host.event",
        "host",
        "implemented",
        "Host EventEngine + HostEventRecorder",
    ),
    PhaseSpec(
        "host.workers.note",
        "host",
        "implemented",
        "WorkerCoordinator note (readiness later in recover)",
    ),
    PhaseSpec(
        "host.system.spawn",
        "host",
        "implemented",
        "Spawn system instance(s) → system schedule",
    ),
    PhaseSpec(
        "host.definitions.load",
        "host",
        "implemented",
        "PalmKernel.load_definitions",
    ),
    PhaseSpec(
        "host.product.wire",
        "host",
        "implemented",
        "CQRS + product services from composition",
    ),
    PhaseSpec(
        "host.surfaces.mount",
        "host",
        "implemented",
        "Mount server surfaces when deployment.server",
        optional=True,
    ),
    PhaseSpec(
        "host.recover",
        "host",
        "implemented",
        "RecoveryCoordinator.recover (mode may skip)",
        optional=True,
    ),
    PhaseSpec(
        "host.ready",
        "host",
        "implemented",
        "Host STARTED + ready mark",
    ),
)

# ── System schedule (BaseRuntime) ────────────────────────────────────────────
# 0.59.3 — full table walked by BaseRuntime.start (all seats implemented).

SYSTEM_PHASES: tuple[PhaseSpec, ...] = (
    PhaseSpec(
        "system.log.ready",
        "system",
        "implemented",
        "Ensure SystemLog is process-ready (early console)",
    ),
    PhaseSpec(
        "system.plugins.ensure",
        "system",
        "implemented",
        "install composition package names",
    ),
    PhaseSpec(
        "system.engines.init",
        "system",
        "implemented",
        "context, event, resource, workload, auth",
    ),
    PhaseSpec(
        "system.storage.select",
        "system",
        "implemented",
        "StorageFactory when storage not yet initialized",
    ),
    PhaseSpec(
        "system.outbox.wire",
        "system",
        "implemented",
        "OutboxStore + reliable events when DNA lists outbox",
        optional=True,
    ),
    PhaseSpec(
        "system.hooks.install",
        "system",
        "implemented",
        "Job hooks + orch/BT/instance_manager initialize",
    ),
    PhaseSpec(
        "system.orchestration.start",
        "system",
        "implemented",
        "orchestration.start — accept jobs",
    ),
    PhaseSpec(
        "system.install.bind",
        "system",
        "implemented",
        "Bind InstallInterface collaborator ports (peer of execution)",
    ),
    PhaseSpec(
        "system.planes.attach",
        "system",
        "implemented",
        "SystemPlanes subsystem: put wait, session, work from install interface",
    ),
    PhaseSpec(
        "system.supervisor.wire",
        "system",
        "implemented",
        "SystemSupervisor seat — continuous services registry (0.60)",
    ),
    PhaseSpec(
        "system.bind",
        "system",
        "implemented",
        "Optional palm provider bind",
        optional=True,
    ),
    PhaseSpec(
        "system.ready",
        "system",
        "implemented",
        "System instance ready mark",
    ),
    PhaseSpec(
        "system.structure.assemble",
        "system",
        "implemented",
        "Structure assemble — load definition, reconcile, publish admission (0.63)",
    ),
    PhaseSpec(
        "system.background.start",
        "system",
        "implemented",
        "Start supervised continuous services (work_drain, …)",
        optional=True,
    ),
)

_HOST_BY_ID = {p.id: p for p in HOST_PHASES}
_SYSTEM_BY_ID = {p.id: p for p in SYSTEM_PHASES}


def host_phase_ids() -> tuple[str, ...]:
    return tuple(p.id for p in HOST_PHASES)


def system_phase_ids() -> tuple[str, ...]:
    return tuple(p.id for p in SYSTEM_PHASES)


def get_phase(phase_id: str) -> PhaseSpec | None:
    return _HOST_BY_ID.get(phase_id) or _SYSTEM_BY_ID.get(phase_id)


def phases_for(schedule: ScheduleName) -> tuple[PhaseSpec, ...]:
    if schedule == "host":
        return HOST_PHASES
    if schedule == "system":
        return SYSTEM_PHASES
    raise ValueError(f"unknown schedule {schedule!r}")


def schedule_catalog() -> dict[str, list[dict[str, object]]]:
    """Doctor / inspect dump of both locked tables."""
    return {
        "host": [p.to_dict() for p in HOST_PHASES],
        "system": [p.to_dict() for p in SYSTEM_PHASES],
    }


__all__ = [
    "HOST_PHASES",
    "SYSTEM_PHASES",
    "PhaseSeat",
    "PhaseSpec",
    "ScheduleName",
    "get_phase",
    "host_phase_ids",
    "phases_for",
    "schedule_catalog",
    "system_phase_ids",
]
