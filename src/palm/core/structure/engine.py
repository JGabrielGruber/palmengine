"""StructureEngine — pure desired-structure reconciler.

No sockets. No OS spawn. No business jobs. System applies effect intents;
clients read admission. Floor: embedded definition with empty places becomes READY
after tick when not blocked.

**0.71.15:** place readiness lives only behind a bound ``ready(place_id)`` hand.
No second ``_places_ready`` set. Unbound hand → places stay missing (fail closed).
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.structure.definition import StructureDefinition
from palm.core.structure.exceptions import StructureEngineError
from palm.core.structure.intent import EffectIntent, EffectIntentKind
from palm.core.structure.observation import Observation, ObservationKind
from palm.core.structure.result import AssembleResult
from palm.core.structure.status import (
    AdmissionSnapshot,
    StructurePhase,
    StructureStatus,
)


class StructureEngine(BasePalmEngine):
    """In-memory structure reconciler (durable projection later in system)."""

    def __init__(self) -> None:
        super().__init__(name="structure")
        self._lock = threading.RLock()
        self._definition: StructureDefinition | None = None
        self._phase: StructurePhase = StructurePhase.EMPTY
        self._place_ready: Callable[[str], bool] | None = None
        self._block_reasons: list[str] = []
        self._truth_home_up: bool = True
        self._pending_ensure: set[str] = set()

    def _do_initialize(self, **options: Any) -> None:
        return

    def _do_shutdown(self) -> None:
        with self._lock:
            self._definition = None
            self._phase = StructurePhase.EMPTY
            self._block_reasons.clear()
            self._truth_home_up = True
            self._pending_ensure.clear()

    # --- public API ---------------------------------------------------------

    def receive_definition(
        self,
        definition: StructureDefinition,
        *,
        force: bool = False,
    ) -> AdmissionSnapshot:
        """Load (or replace) desired structure. Resets readiness under new law.

        When the same id/version is already READY, returns without reset unless
        *force* is True (0.63.18 reassemble edge — external structure change).
        """
        if not definition.id:
            raise StructureEngineError("structure definition id must be non-empty")
        with self._lock:
            same = (
                not force
                and self._definition is not None
                and self._definition.id == definition.id
                and self._definition.version == definition.version
                and self._phase is StructurePhase.READY
            )
            if same:
                return self._status_unlocked().admission()

            had_ready = self._phase is StructurePhase.READY
            self._definition = definition
            self._block_reasons.clear()
            self._truth_home_up = True
            self._pending_ensure.clear()
            self._phase = (
                StructurePhase.INVALIDATED if had_ready else StructurePhase.RECEIVED
            )
            return self._status_unlocked().admission()

    def invalidate(self, *, reason: str = "invalidated") -> AdmissionSnapshot:
        """Void current readiness; keep definition. Requires reassemble to recover."""
        with self._lock:
            if self._definition is None:
                self._phase = StructurePhase.EMPTY
                return self._status_unlocked().admission()
            if self._phase is not StructurePhase.EMPTY:
                self._phase = StructurePhase.INVALIDATED
                # reason is visible via phase; optional note for callers
                _ = reason
            return self._status_unlocked().admission()

    def observe(self, observation: Observation) -> AdmissionSnapshot:
        """Fold one structure fact. Does not apply effects (call tick)."""
        with self._lock:
            self._apply_observation_unlocked(observation)
            return self._status_unlocked().admission()

    def bind_place_ready(self, ready: Callable[[str], bool] | None) -> None:
        """Bind assemble place readiness (registry / port ``ready``). None = none ready."""
        with self._lock:
            self._place_ready = ready

    def tick(self) -> AssembleResult:
        """Reconcile once: emit intents, advance phase when facts allow."""
        with self._lock:
            before = self._status_unlocked()
            intents: list[EffectIntent] = []
            notes: list[str] = []

            if self._definition is None:
                status = self._status_unlocked()
                admission = status.admission()
                return AssembleResult(
                    status=status,
                    admission=admission,
                    intents=(),
                    changed=False,
                    notes=("no_definition",),
                )

            # Truth home down blocks business even if places look ready.
            if not self._truth_home_up:
                self._phase = StructurePhase.BLOCKED
                if "truth_home_down" not in self._block_reasons:
                    self._block_reasons.append("truth_home_down")
                status = self._status_unlocked()
                admission = status.admission()
                return AssembleResult(
                    status=status,
                    admission=admission,
                    intents=(),
                    changed=before.phase != status.phase
                    or before.admission().may_run_business != admission.may_run_business,
                    notes=("blocked_truth_home",),
                )

            # Clear truth_home block if up again
            self._block_reasons = [r for r in self._block_reasons if r != "truth_home_down"]

            if self._phase in (
                StructurePhase.RECEIVED,
                StructurePhase.INVALIDATED,
                StructurePhase.BLOCKED,
            ):
                # Leave BLOCKED only when block_reasons empty after filter above
                if self._phase is StructurePhase.BLOCKED and self._block_reasons:
                    status = self._status_unlocked()
                    admission = status.admission()
                    return AssembleResult(
                        status=status,
                        admission=admission,
                        intents=(),
                        changed=False,
                        notes=("still_blocked",),
                    )
                self._phase = StructurePhase.ASSEMBLING
                notes.append("enter_assembling")

            missing = self._missing_places_unlocked()
            for place in missing:
                if place not in self._pending_ensure:
                    intents.append(
                        EffectIntent(
                            kind=EffectIntentKind.ENSURE_PLACE,
                            target=place,
                        )
                    )
                    self._pending_ensure.add(place)
                    notes.append(f"ensure_place:{place}")

            if missing:
                self._phase = StructurePhase.ASSEMBLING
            else:
                # No places (embedded floor) or all places ready → definition-ready
                self._phase = StructurePhase.READY
                self._pending_ensure.clear()
                notes.append("definition_ready")

            status = self._status_unlocked()
            admission = status.admission()
            changed = (
                before.phase != status.phase
                or before.admission().may_run_business != admission.may_run_business
                or bool(intents)
            )
            return AssembleResult(
                status=status,
                admission=admission,
                intents=tuple(intents),
                changed=changed,
                notes=tuple(notes),
            )

    def status(self) -> StructureStatus:
        with self._lock:
            return self._status_unlocked()

    def admission(self) -> AdmissionSnapshot:
        with self._lock:
            return self._status_unlocked().admission()

    def definition(self) -> StructureDefinition | None:
        with self._lock:
            return self._definition

    # --- internals ----------------------------------------------------------

    def _is_place_ready_unlocked(self, place_id: str) -> bool:
        hand = self._place_ready
        if hand is None:
            return False
        return bool(hand(place_id))

    def _places_ready_view_unlocked(self) -> frozenset[str]:
        definition = self._definition
        if definition is None:
            return frozenset()
        return frozenset(
            p for p in definition.places_required if self._is_place_ready_unlocked(p)
        )

    def _missing_places_unlocked(self) -> tuple[str, ...]:
        if self._definition is None:
            return ()
        required = self._definition.places_required
        return tuple(p for p in required if not self._is_place_ready_unlocked(p))

    def _status_unlocked(self) -> StructureStatus:
        definition = self._definition
        missing = self._missing_places_unlocked()
        return StructureStatus(
            phase=self._phase,
            definition_id=definition.id if definition else None,
            definition_version=definition.version if definition else None,
            places_ready=self._places_ready_view_unlocked(),
            places_missing=missing,
            block_reasons=tuple(self._block_reasons),
            truth_home_up=self._truth_home_up,
        )

    def _apply_observation_unlocked(self, observation: Observation) -> None:
        kind = observation.kind
        target = observation.target

        if kind is ObservationKind.PLACE_READY:
            if target:
                # Readiness truth is the bound hand — observation clears pending only.
                self._pending_ensure.discard(target)
            # Drop place_failed for this target
            self._block_reasons = [
                r
                for r in self._block_reasons
                if r != f"place_failed:{target}"
            ]
        elif kind is ObservationKind.PLACE_FAILED:
            if target:
                reason = f"place_failed:{target}"
                if reason not in self._block_reasons:
                    self._block_reasons.append(reason)
                self._phase = StructurePhase.BLOCKED
        elif kind is ObservationKind.PLACE_GONE:
            if target:
                if self._phase is StructurePhase.READY:
                    self._phase = StructurePhase.INVALIDATED
        elif kind is ObservationKind.TRUTH_HOME_UP:
            self._truth_home_up = True
            self._block_reasons = [
                r for r in self._block_reasons if r != "truth_home_down"
            ]
        elif kind is ObservationKind.TRUTH_HOME_DOWN:
            self._truth_home_up = False
            if "truth_home_down" not in self._block_reasons:
                self._block_reasons.append("truth_home_down")
            if self._phase is StructurePhase.READY:
                self._phase = StructurePhase.BLOCKED
        elif kind is ObservationKind.PROJECTION_FAILED:
            reason = f"projection_failed:{target or 'default'}"
            if reason not in self._block_reasons:
                self._block_reasons.append(reason)
            if self._phase is StructurePhase.READY:
                self._phase = StructurePhase.BLOCKED
        elif kind is ObservationKind.PROJECTION_LOADED:
            # Floor: no projection required; clear matching fail reason
            reason = f"projection_failed:{target or 'default'}"
            self._block_reasons = [r for r in self._block_reasons if r != reason]
        elif kind is ObservationKind.STRUCTURE_SEED_FAILED:
            reason = "structure_seed_failed"
            if reason not in self._block_reasons:
                self._block_reasons.append(reason)
            self._phase = StructurePhase.BLOCKED
        elif kind is ObservationKind.STRUCTURE_SEED_FINISHED:
            self._block_reasons = [
                r for r in self._block_reasons if r != "structure_seed_failed"
            ]
        elif kind is ObservationKind.STRUCTURE_POLICY_VIOLATION:
            reason = target or "refuse:policy"
            if reason not in self._block_reasons:
                self._block_reasons.append(reason)
            self._phase = StructurePhase.BLOCKED
        elif kind is ObservationKind.STRUCTURE_POLICY_CLEARED:
            if target:
                self._block_reasons = [
                    r for r in self._block_reasons if r != target
                ]
            else:
                self._block_reasons = [
                    r for r in self._block_reasons if not r.startswith("refuse:")
                ]
        elif kind is ObservationKind.SEAT_BOUND:
            pass  # optional floor; no phase change yet
        else:
            # Exhaustiveness for future kinds — ignore unknown safely
            pass


__all__ = ["StructureEngine"]
