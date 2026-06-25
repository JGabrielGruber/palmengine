"""Declarative behavior-tree construction for the collection step subtree."""

from __future__ import annotations

from palm.core.behavior_tree import BaseNode
from palm.patterns.wizard.flow.collection.state import collection_phase
from palm.patterns.wizard.flow.phases._base import WizardPhaseContext
from palm.patterns.wizard.bindings.behavior_tree.bt import PhaseKeyedSelectorNode, PhaseTransitionLoopNode
from palm.patterns.wizard.flow.collection.phases.fields import build_fields_phase
from palm.patterns.wizard.flow.collection.phases.menu import build_menu_phase
from palm.patterns.wizard.flow.collection.phases.remove import build_remove_phase
from palm.patterns.wizard.flow.collection.phases.select import build_select_phase


def build_collection_subtree(ctx: WizardPhaseContext) -> BaseNode:
    """
    Return the routed collection subtree for one wizard step.

    Tree shape::

        PhaseTransitionLoopNode
          └─ PhaseKeyedSelectorNode
               ├─ menu
               ├─ select_item
               ├─ field
               └─ remove_confirm
    """
    selector = PhaseKeyedSelectorNode(
        f"{ctx.step.slug}_phases",
        resolve_phase=collection_phase,
        default_phase="menu",
        phases={
            "menu": build_menu_phase(ctx),
            "select_item": build_select_phase(ctx),
            "field": build_fields_phase(ctx),
            "remove_confirm": build_remove_phase(ctx),
        },
    )
    return PhaseTransitionLoopNode(
        f"{ctx.step.slug}_router",
        child=selector,
        resolve_phase=collection_phase,
    )