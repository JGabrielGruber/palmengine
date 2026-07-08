"""Branch step — BT-routed conditional subtree registered in the wizard sequence."""

from __future__ import annotations

from palm.core.behavior_tree import DecoratorNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.flow.branch.phases.tree import build_branch_subtree
from palm.patterns.wizard.flow.phases._base import WizardPhaseContext


class BranchStepNode(DecoratorNode):
    """Top-level branch step registered in the wizard sequence."""

    def __init__(self, ctx: WizardPhaseContext) -> None:
        from palm.patterns.wizard.flow.extensions.registry import default_wizard_step_registry

        super().__init__(
            ctx.step.slug,
            child=build_branch_subtree(ctx, registry=default_wizard_step_registry()),
        )
        self._ctx = ctx

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        return self.child.tick(state)


def build_branch_phase(ctx: WizardPhaseContext) -> BranchStepNode:
    return BranchStepNode(ctx)