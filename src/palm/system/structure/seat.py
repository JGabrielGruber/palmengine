"""Structure seat — engine + effect port + published admission on the shell."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace

from palm.core.structure import (
    AdmissionSnapshot,
    Observation,
    ObservationKind,
    StructureDefinition,
    StructureEngine,
    StructureStatus,
    local_embedded,
    refuse_violations,
)
from palm.system.structure.effects import EffectPort
from palm.system.structure.hands import CapabilitySeats
from palm.system.structure.loop import (
    DEFAULT_MAX_TICKS,
    AssembleLoopResult,
    assemble_until_steady,
)
from palm.system.structure.place_registry import PlaceEffectPort
from palm.system.structure.structure_effects import StructureEffectPort


@dataclass
class StructureSeat:
    """System-owned structure organ (not product control)."""

    engine: StructureEngine = field(default_factory=StructureEngine)
    effects: EffectPort = field(default_factory=StructureEffectPort)
    last_loop: AssembleLoopResult | None = None
    definition: StructureDefinition | None = None
    materialized_capabilities: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.engine.is_initialized:
            self.engine.initialize()
        self._bind_place_ready_hand()

    def _bind_place_ready_hand(self) -> None:
        """Prefer place-registry ``ready`` over folding PLACE_READY into a second book."""
        match self.effects:
            case StructureEffectPort() as port:
                self.engine.bind_place_ready(port.registry.ready)
            case PlaceEffectPort() as port:
                self.engine.bind_place_ready(port.registry.ready)
            case _:
                self.engine.bind_place_ready(None)

    def admission(self) -> AdmissionSnapshot:
        snap = self.engine.admission()
        caps = self.materialized_capabilities
        if snap.capabilities == caps:
            return snap
        return replace(snap, capabilities=caps)

    def status(self) -> StructureStatus:
        return self.engine.status()

    def assemble(
        self,
        definition: StructureDefinition | None = None,
        *,
        max_ticks: int = DEFAULT_MAX_TICKS,
        surfaces: Iterable[str] = (),
        force: bool = False,
    ) -> AssembleLoopResult:
        """Structure assemble: load definition (default embedded) and reconcile until steady.

        When *surfaces* are provided, definition refuse is checked (0.63.6).
        ``work_drain`` membership is definition ``capabilities`` (omit is enough).
        Violations block admission — fail closed, no soft dual.

        *force* voids same-id READY and re-converges (0.63.18 reassemble edge).
        Membership is always re-evaluated: prior refuse reasons clear first.
        """
        if definition is None:
            definition = local_embedded()
        self.definition = definition
        self._bind_place_ready_hand()
        bind = getattr(self.effects, "bind_structure", None)
        if callable(bind):
            bind(definition, surfaces=surfaces)
        # Honest membership re-check before / after definition load.
        self.engine.observe(
            Observation(kind=ObservationKind.STRUCTURE_POLICY_CLEARED)
        )
        self.engine.receive_definition(definition, force=force)
        for reason in refuse_violations(definition, surfaces=surfaces):
            self.engine.observe(
                Observation(
                    kind=ObservationKind.STRUCTURE_POLICY_VIOLATION,
                    target=reason,
                )
            )
        result = assemble_until_steady(
            self.engine,
            self.effects,
            max_ticks=max_ticks,
        )
        self.last_loop = result
        return result

    def materialize(self, seats: CapabilitySeats) -> frozenset[str]:
        """Apply local capability membership from loaded definition onto *seats*."""
        from palm.system.structure.materialize import apply_local_capabilities

        applied = apply_local_capabilities(self.definition, seats)
        self.materialized_capabilities = applied
        return applied

    def reassemble(
        self,
        definition: StructureDefinition | None = None,
        *,
        max_ticks: int = DEFAULT_MAX_TICKS,
        surfaces: Iterable[str] = (),
        force: bool = False,
    ) -> AssembleLoopResult:
        """Re-converge after definition or membership change (0.63.18).

        Uses the current seat definition when *definition* is omitted.
        Fails closed while invalidated/blocked; business paths that need admission must not soft-skip.
        """
        if definition is None:
            definition = (
                self.definition if self.definition is not None else local_embedded()
            )
        return self.assemble(
            definition,
            max_ticks=max_ticks,
            surfaces=surfaces,
            force=force,
        )

    def reset(self) -> None:
        self.engine.shutdown()
        self.engine.initialize()
        self._bind_place_ready_hand()
        self.last_loop = None
        self.definition = None
        self.materialized_capabilities = frozenset()


__all__ = ["StructureSeat"]
