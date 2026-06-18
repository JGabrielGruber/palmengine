"""Collection step — BT-routed multi-phase subtree registered in the wizard sequence."""

from __future__ import annotations

from palm.core.behavior_tree import DecoratorNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.phases._base import WizardPhaseContext
from palm.patterns.wizard.phases.collection.tree import build_collection_subtree


class CollectionStepNode(DecoratorNode):
    """Top-level collection step registered in the wizard sequence."""

    def __init__(self, ctx: WizardPhaseContext) -> None:
        super().__init__(ctx.step.slug, child=build_collection_subtree(ctx))
        self._ctx = ctx

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        return self.child.tick(state)


def build_collection_phase(ctx: WizardPhaseContext) -> CollectionStepNode:
    return CollectionStepNode(ctx)