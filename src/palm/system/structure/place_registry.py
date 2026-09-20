"""In-process place registry — structure effect hands for ENSURE/RELEASE place (0.63.11+).

Registry of places this process can mark ready so a definition with
places_required can converge. **0.63.14:** optional :class:`PlaceSpawnPort`
grows bodies (OS / workload strategies); default remains in-process success.

**0.71.2 / 0.71.9:** when a workload book is bound, ``places`` is a **projection**
of that book only — no overlay dict beside it. Unbound, one local register
holds bare / ``os:`` ready rows. Failed ensures are observations, not rows.

**0.71.7:** ``engine_from_spawn`` matches typed ``RegisteredPlaceSpawn`` (same
invert as ``host_bind.book_bind_port``); no Protocol ``isinstance``.

**0.71.11:** ``ready(place_id)`` is the assemble readiness hand (book projection
or local assemble ack). StructureEngine binds it; it does not keep a second
body book of place observations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from palm.core.structure import EffectIntent, EffectIntentKind, Observation, ObservationKind
from palm.core.workload.engine import WorkloadEngine
from palm.core.workload.exceptions import WorkloadNotFoundError
from palm.core.workload.record import Workload
from palm.core.workload.status import WorkloadStatus, is_terminal
from palm.system.structure.place_spawn import (
    InProcessPlaceSpawn,
    PlaceSpawnPort,
    RegisteredPlaceSpawn,
)

PlaceState = Literal["ready", "failed", "gone"]


def engine_from_spawn(spawn: object) -> WorkloadEngine | None:
    """Return the WorkloadEngine from typed RegisteredPlaceSpawn binds, if any."""
    match spawn:
        case RegisteredPlaceSpawn() as registered:
            return registered.book_engine()
        case _:
            return None


def _place_id_for(workload: Workload) -> str:
    labeled = str(workload.spec.labels.get("structure_place") or "").strip()
    if labeled:
        return labeled
    return str(workload.workload_id or "").strip()


def _project_state(workload: Workload) -> PlaceState | None:
    status = workload.status
    if status is WorkloadStatus.FAILED:
        return "failed"
    if is_terminal(status):
        return None
    return "ready"


@dataclass
class InProcessPlaceRegistry:
    """Structure place view: one local register, or workload-book projection."""

    _local: dict[str, PlaceState] = field(default_factory=dict)
    book: WorkloadEngine | None = None

    @property
    def places(self) -> dict[str, PlaceState]:
        """Book projection when bound; otherwise the local register."""
        if self._book_is_home():
            return self._project_book()
        return dict(self._local)

    def bind_book(self, book: WorkloadEngine | None) -> None:
        self.book = book

    def _book_is_home(self) -> bool:
        book = self.book
        return book is not None and book.is_initialized

    def mark(self, place_id: str, state: PlaceState) -> None:
        """Write the local assemble register (bare / os: ack; not a body book)."""
        key = str(place_id or "").strip()
        if not key:
            return
        if state == "gone":
            self._local.pop(key, None)
        else:
            self._local[key] = state

    def release(self, place_id: str) -> PlaceState:
        key = str(place_id or "").strip()
        if not key:
            return "gone"
        self._local.pop(key, None)
        return "gone"

    def ready(self, place_id: str) -> bool:
        """Assemble readiness: book projection wins; else local assemble ack."""
        key = str(place_id or "").strip()
        if not key:
            return False
        if self._book_is_home():
            projected = self._project_book()
            if key in projected:
                return projected[key] == "ready"
            book = self.book
            if book is not None:
                try:
                    book.get(key)
                except WorkloadNotFoundError:
                    pass
                else:
                    # Known to the body book but not ready in projection.
                    return False
            return self._local.get(key) == "ready"
        return self._local.get(key) == "ready"

    def _project_book(self) -> dict[str, PlaceState]:
        projected: dict[str, PlaceState] = {}
        book = self.book
        if book is None or not book.is_initialized:
            return projected
        try:
            rows = book.list()
        except Exception:
            rows = []
        for workload in rows:
            place_id = _place_id_for(workload)
            if not place_id:
                continue
            state = _project_state(workload)
            if state is not None:
                projected[place_id] = state
        return projected


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
            # Spawn hands first. Ready marks the assemble register (0.71.11).
            # Failed ensures stay observations (0.71.3+). places stays book-only
            # when the workload book is home (0.71.9).
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
