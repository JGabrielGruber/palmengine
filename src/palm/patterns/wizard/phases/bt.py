"""
Reusable behavior-tree primitives for wizard phase routing.

These composites keep multi-phase steps (e.g. collection) declarative: children
are independent leaves keyed by blackboard state, and a transition loop
re-ticks within a single wizard tick when the active phase changes.
"""

from __future__ import annotations

from collections.abc import Callable

from palm.core.behavior_tree import BaseNode, PatternStatus
from palm.core.behavior_tree.composite import CompositeNode
from palm.core.behavior_tree.decorator import DecoratorNode
from palm.core.context import BaseState

PhaseKeyResolver = Callable[[BaseState], str]
_DEFAULT_MAX_TRANSITIONS = 16


def phase_transition() -> PatternStatus:
    """Signal the transition loop to dispatch another phase in the same tick."""
    return PatternStatus.RUNNING


class PhaseKeyedSelectorNode(CompositeNode):
    """Tick exactly one child keyed by ``resolve_phase(state)``."""

    def __init__(
        self,
        name: str,
        *,
        resolve_phase: PhaseKeyResolver,
        phases: dict[str, BaseNode],
        default_phase: str,
    ) -> None:
        if default_phase not in phases:
            raise ValueError(f"default_phase {default_phase!r} missing from phases")
        super().__init__(name, children=list(phases.values()))
        self._resolve_phase = resolve_phase
        self._phases = phases
        self._default_phase = default_phase

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        phase = self._resolve_phase(state)
        child = self._phases.get(phase)
        if child is None:
            child = self._phases[self._default_phase]
        return child.tick(state)


class PhaseTransitionLoopNode(DecoratorNode):
    """
    Re-tick ``child`` while the active phase changes within one outer tick.

    Phase leaves return :attr:`PatternStatus.RUNNING` to request an immediate
    re-dispatch (for example menu → field → menu) without overloading FAILURE.
    """

    def __init__(
        self,
        name: str,
        child: BaseNode,
        *,
        resolve_phase: PhaseKeyResolver,
        max_transitions: int = _DEFAULT_MAX_TRANSITIONS,
    ) -> None:
        super().__init__(name, child=child)
        self._resolve_phase = resolve_phase
        self._max_transitions = max_transitions

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        for _ in range(self._max_transitions):
            phase_before = self._resolve_phase(state)
            status = self.child.tick(state)
            phase_after = self._resolve_phase(state)

            if status in (PatternStatus.WAITING_FOR_INPUT, PatternStatus.SUCCESS, PatternStatus.FAILURE):
                return status
            if status == PatternStatus.RUNNING and phase_after != phase_before:
                continue
            return status

        return PatternStatus.FAILURE