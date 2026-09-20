"""In-process place registry — structure effect hands for ENSURE/RELEASE place (0.63.11+).

Registry of places this process can mark ready so a definition with
places_required can converge. **0.63.14:** optional :class:`PlaceSpawnPort`
grows bodies (OS / workload strategies); default remains in-process success.

**0.71.2:** when a workload book is bound, adopted and ``workload:`` readiness
is a **projection** of that book. The overlay is only for bare / ``os:`` ids
and failed ensures that never entered the book. Not Grove.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from palm.core.structure import EffectIntent, EffectIntentKind, Observation, ObservationKind
from palm.core.workload.status import WorkloadStatus, is_terminal
from palm.system.structure.place_spawn import InProcessPlaceSpawn, PlaceSpawnPort

PlaceState = Literal["ready", "failed", "gone"]

#: Spawn-port handle keys that carry a WorkloadEngine (register, not a place-id if).
_BOOK_HANDLE_KEYS = ("__adopt_spawn__", "__workload_spawn__")


def engine_from_spawn(spawn: Any) -> Any | None:
    """Return the WorkloadEngine stashed on a registered spawn port, if any."""
    handles = getattr(spawn, "handles", None)
    if not isinstance(handles, dict):
        return None
    for key in _BOOK_HANDLE_KEYS:
        hands = handles.get(key)
        engine = getattr(hands, "engine", None)
        if engine is not None:
            return engine
    return None


def _place_id_for(workload: Any) -> str:
    spec = getattr(workload, "spec", None)
    labels = getattr(spec, "labels", None) or {}
    labeled = str(labels.get("structure_place") or "").strip()
    if labeled:
        return labeled
    return str(getattr(workload, "workload_id", "") or "").strip()


def _project_state(workload: Any) -> PlaceState | None:
    status = getattr(workload, "status", None)
    if status is WorkloadStatus.FAILED:
        return "failed"
    if status is None or is_terminal(status):
        return None
    return "ready"


@dataclass
class InProcessPlaceRegistry:
    """Structure place view: overlay plus optional workload-book projection."""

    overlay: dict[str, PlaceState] = field(default_factory=dict)
    book: Any | None = None

    @property
    def places(self) -> dict[str, PlaceState]:
        """Merged view. Book rows win for ids the engine still tracks."""
        return self._projected()

    def bind_book(self, book: Any | None) -> None:
        self.book = book

    def mark(self, place_id: str, state: PlaceState) -> None:
        key = str(place_id or "").strip()
        if not key:
            return
        if state == "gone":
            self.overlay.pop(key, None)
        else:
            self.overlay[key] = state

    def release(self, place_id: str) -> PlaceState:
        key = str(place_id or "").strip()
        if not key:
            return "gone"
        self.overlay.pop(key, None)
        return "gone"

    def _projected(self) -> dict[str, PlaceState]:
        live: set[str] = set()
        projected: dict[str, PlaceState] = {}
        book = self.book
        if book is not None and getattr(book, "is_initialized", False):
            try:
                rows = book.list()
            except Exception:
                rows = []
            for workload in rows:
                place_id = _place_id_for(workload)
                if not place_id:
                    continue
                live.add(place_id)
                state = _project_state(workload)
                if state is not None:
                    projected[place_id] = state
        out = {key: state for key, state in self.overlay.items() if key not in live}
        out.update(projected)
        return out


@dataclass
class PlaceEffectPort:
    """Apply structure place intents against the registry + optional spawn port (0.63.14)."""

    registry: InProcessPlaceRegistry = field(default_factory=InProcessPlaceRegistry)
    spawn: PlaceSpawnPort = field(default_factory=InProcessPlaceSpawn)
    applied: list[EffectIntent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.bind_book_from_spawn()

    def bind_book_from_spawn(self) -> None:
        engine = engine_from_spawn(self.spawn)
        if engine is not None:
            self.registry.bind_book(engine)

    def apply(self, intent: EffectIntent) -> tuple[Observation, ...]:
        self.bind_book_from_spawn()
        self.applied.append(intent)
        kind = intent.kind
        target = str(intent.target or "").strip()

        if kind is EffectIntentKind.ENSURE_PLACE:
            if not target:
                return (
                    Observation(
                        kind=ObservationKind.PLACE_FAILED,
                        target="",
                        payload={"reason": "empty_place_id"},
                    ),
                )
            # Spawn hands first (structure body); registry records the outcome.
            result = self.spawn.ensure(target, payload=dict(intent.payload or {}))
            if result.state == "ready":
                self.registry.mark(target, "ready")
                return (
                    Observation(
                        kind=ObservationKind.PLACE_READY,
                        target=target,
                        payload={"spawn": result.reason, **dict(result.payload)},
                    ),
                )
            self.registry.mark(target, "failed")
            return (
                Observation(
                    kind=ObservationKind.PLACE_FAILED,
                    target=target,
                    payload={
                        "reason": result.reason or result.state,
                        **dict(result.payload),
                    },
                ),
            )

        if kind is EffectIntentKind.RELEASE_PLACE:
            if target:
                result = self.spawn.release(target)
                self.registry.release(target)
                return (
                    Observation(
                        kind=ObservationKind.PLACE_GONE,
                        target=target,
                        payload={"spawn": result.reason},
                    ),
                )
            return ()

        # Other structure intents: recorded, no observation yet (growth).
        return ()


__all__ = [
    "InProcessPlaceRegistry",
    "PlaceEffectPort",
    "PlaceState",
    "engine_from_spawn",
]
