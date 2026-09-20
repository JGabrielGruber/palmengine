"""Host structure bind — wire shell WorkloadEngine into structure place hands (0.63.17).

Default place-effect hands stay in-process for bare places. Host assemble upgrades
them to the combined ``os:`` + ``workload:`` spawn port and binds the live
engine when it is initialized.

**Opt-in:** on by default when the engine is ready; off via
``structure_bind_workload=False``. Does not force composition membership.
Does not replace custom effect ports without a place registry.
"""

from __future__ import annotations

from typing import Any

from palm.system.structure.place_registry import PlaceEffectPort
from palm.system.structure.place_spawn import BookBindPort
from palm.system.structure.seat import StructureSeat
from palm.system.structure.structure_effects import StructureEffectPort
from palm.system.structure.workload_place import (
    WorkloadPlaceSpawn,
    combined_structure_spawn_port,
)


def resolve_workload_engine(shell: Any) -> Any | None:
    """Return shell.workload when present and initialized; else None."""
    engine = getattr(shell, "workload", None)
    if engine is None:
        return None
    if not getattr(engine, "is_initialized", False):
        return None
    return engine


def place_effect_port(effects: Any) -> PlaceEffectPort | None:
    """Extract the place-effect hands from StructureEffectPort or bare place effects."""
    if isinstance(effects, PlaceEffectPort):
        return effects
    places = getattr(effects, "places", None)
    if isinstance(places, PlaceEffectPort):
        return places
    return None


def book_bind_port(spawn: Any) -> BookBindPort | None:
    """Return spawn when it exposes typed book binds."""
    if isinstance(spawn, BookBindPort):
        return spawn
    return None


def workload_spawn_hands(spawn: Any) -> WorkloadPlaceSpawn | None:
    """Find WorkloadPlaceSpawn among typed book binds (if any)."""
    port = book_bind_port(spawn)
    if port is None:
        return None
    for hands in port.book_binds():
        if isinstance(hands, WorkloadPlaceSpawn):
            return hands
    return None


def bind_host_structure_to_seat(
    seat: StructureSeat,
    shell: Any,
    *,
    bind_workload: bool = True,
) -> dict[str, Any]:
    """Upgrade default place hands and optionally bind shell WorkloadEngine.

    Returns a small report for logs and tests::

        {
          "bound": bool,           # spawn port mutated or engine attached
          "engine": bool,          # live engine bound
          "spawn": str,            # combined | existing | unchanged
          "skipped": str | None,   # why no work (no_place_effects, …)
        }
    """
    report: dict[str, Any] = {
        "bound": False,
        "engine": False,
        "spawn": "unchanged",
        "skipped": None,
    }
    port = place_effect_port(seat.effects)
    if port is None:
        report["skipped"] = "no_place_effects"
        return report

    engine = resolve_workload_engine(shell) if bind_workload else None
    bind = book_bind_port(port.spawn)
    if bind is not None and bind.book_binds():
        current = bind.book_engine()
        if engine is not None and current is not engine:
            bind.bind_book(engine)
            port.bind_book_from_spawn()
            report["bound"] = True
            report["engine"] = True
            report["spawn"] = "existing"
            return report
        if engine is not None and current is engine:
            bind.bind_book(engine)
            port.bind_book_from_spawn()
            report["bound"] = True
            report["engine"] = True
            report["spawn"] = "already"
            return report
        # Hands present but no engine (or bind disabled) — leave fail-closed.
        report["skipped"] = (
            "bind_disabled" if not bind_workload else "engine_not_ready"
        )
        report["spawn"] = "existing"
        return report

    # Default / pre-installed without workload hands → combined.
    port.spawn = combined_structure_spawn_port(engine=engine)
    port.bind_book_from_spawn()
    report["bound"] = True
    report["engine"] = engine is not None
    report["spawn"] = "combined"
    if engine is None and bind_workload:
        report["skipped"] = "engine_not_ready"
    elif not bind_workload:
        report["skipped"] = "bind_disabled"
    return report


def default_structure_effects(*, engine: Any | None = None) -> StructureEffectPort:
    """Default place-effect hands with combined structure spawn (os: + workload:)."""
    return StructureEffectPort(
        places=PlaceEffectPort(spawn=combined_structure_spawn_port(engine=engine))
    )


__all__ = [
    "bind_host_structure_to_seat",
    "book_bind_port",
    "default_structure_effects",
    "place_effect_port",
    "resolve_workload_engine",
    "workload_spawn_hands",
]
