"""Collection step — phase router with internal transition loop."""

from __future__ import annotations

from palm.core.behavior_tree import LeafNode
from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.context import BaseState
from palm.patterns.wizard.collection_state import collection_phase
from palm.patterns.wizard.phases._base import WizardPhaseContext, consume_wizard_input
from palm.patterns.wizard.phases.collection._base import CollectionPhaseContext, CollectionPhaseLeaf
from palm.patterns.wizard.phases.collection.fields import CollectionFieldsPhase
from palm.patterns.wizard.phases.collection.menu import CollectionMenuPhase
from palm.patterns.wizard.phases.collection.remove import CollectionRemovePhase
from palm.patterns.wizard.phases.collection.select import CollectionSelectPhase

_MAX_TRANSITIONS = 16


class CollectionStepNode(LeafNode):
    """
    Top-level collection step registered in the wizard sequence.

    Dispatches to sub-phase leaves and supports intra-tick phase transitions
    (e.g. menu → field → menu) without custom orchestration in ``WizardPattern``.
    """

    def __init__(self, ctx: WizardPhaseContext) -> None:
        super().__init__(ctx.step.slug)
        self._ctx = ctx
        self._phases = _build_collection_phases(CollectionPhaseContext.from_wizard(ctx))

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        pending = consume_wizard_input(state, self._ctx.step.slug)
        for _ in range(_MAX_TRANSITIONS):
            phase = collection_phase(state) or CollectionMenuPhase.phase_key
            phase_leaf = self._phases.get(phase, self._phases[CollectionMenuPhase.phase_key])
            status = phase_leaf.run(state, pending)
            pending = None
            if status != PatternStatus.FAILURE:
                return status
            if phase == (collection_phase(state) or CollectionMenuPhase.phase_key):
                return status
        return PatternStatus.FAILURE


def _build_collection_phases(
    ctx: CollectionPhaseContext,
) -> dict[str, CollectionPhaseLeaf]:
    fields = CollectionFieldsPhase(ctx)
    remove = CollectionRemovePhase(ctx)
    select = CollectionSelectPhase(ctx, fields_phase=fields, remove_phase=remove)
    menu = CollectionMenuPhase(ctx, fields_phase=fields, select_phase=select, remove_phase=remove)
    return {
        CollectionMenuPhase.phase_key: menu,
        CollectionSelectPhase.phase_key: select,
        CollectionFieldsPhase.phase_key: fields,
        CollectionRemovePhase.phase_key: remove,
    }


def build_collection_phase(ctx: WizardPhaseContext) -> CollectionStepNode:
    return CollectionStepNode(ctx)


WizardCollectionLeaf = CollectionStepNode