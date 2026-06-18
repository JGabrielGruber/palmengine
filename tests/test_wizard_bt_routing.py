"""Tests for wizard phase routing behavior-tree primitives."""

from __future__ import annotations

from palm.core.behavior_tree import ActionNode, PatternStatus
from palm.patterns.wizard.collection_state import collection_phase, set_collection_phase
from palm.patterns.wizard.phases.bt import PhaseKeyedSelectorNode, PhaseTransitionLoopNode
from palm.states import BlackboardState


def test_phase_keyed_selector_dispatches_active_phase() -> None:
    state = BlackboardState()
    set_collection_phase(state, "field")
    selector = PhaseKeyedSelectorNode(
        "phases",
        resolve_phase=collection_phase,
        default_phase="menu",
        phases={
            "menu": ActionNode("menu", action=lambda _s: PatternStatus.FAILURE),
            "field": ActionNode("field", action=lambda _s: PatternStatus.SUCCESS),
        },
    )
    assert selector.tick(state) == PatternStatus.SUCCESS


def test_phase_transition_loop_follows_blackboard_phase_changes() -> None:
    state = BlackboardState()
    calls: list[str] = []

    def menu_tick(_state: BaseState) -> PatternStatus:
        calls.append("menu")
        set_collection_phase(_state, "field")
        return PatternStatus.RUNNING

    def field_tick(_state: BaseState) -> PatternStatus:
        calls.append("field")
        return PatternStatus.WAITING_FOR_INPUT

    selector = PhaseKeyedSelectorNode(
        "phases",
        resolve_phase=collection_phase,
        default_phase="menu",
        phases={
            "menu": ActionNode("menu", action=menu_tick),
            "field": ActionNode("field", action=field_tick),
        },
    )
    router = PhaseTransitionLoopNode("router", child=selector, resolve_phase=collection_phase)

    assert router.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert calls == ["menu", "field"]
    assert collection_phase(state) == "field"