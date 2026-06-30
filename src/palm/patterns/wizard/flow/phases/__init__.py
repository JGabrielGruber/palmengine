"""
Wizard phases — BT-native step implementations.

BT composites and sequence navigation live in
:mod:`palm.patterns.wizard.bindings.behavior_tree`. Collection subtrees live in
:mod:`palm.patterns.wizard.flow.collection`. Step-kind registration lives in
:mod:`palm.patterns.wizard.flow.extensions`.

Each wizard step kind maps to a dedicated phase module that builds behavior-tree
nodes. ``WizardPattern`` itself only binds context and ticks the root tree.
"""

from palm.patterns.wizard.flow.phases._base import (
    EventEmitter,
    WizardPhaseContext,
    provide_wizard_input,
)
from palm.patterns.wizard.bindings.behavior_tree.backtrack import (
    WizardCompletionGuardNode,
    WizardSequenceNode,
    apply_backtrack,
    backtrack_notifier,
    can_backtrack_to,
    request_backtrack,
)
from palm.patterns.wizard.bindings.behavior_tree.bt import (
    PhaseKeyedSelectorNode,
    PhaseTransitionLoopNode,
    phase_transition,
)
from palm.patterns.wizard.flow.collection.phases.step import CollectionStepNode
from palm.patterns.wizard.flow.phases.commit import WizardCommitLeaf
from palm.patterns.wizard.flow.phases.input import WizardInputLeaf
from palm.patterns.wizard.flow.extensions.registry import (
    WizardStepKindRegistry,
    default_wizard_step_registry,
    register_builtin_wizard_step_kinds,
)
from palm.patterns.wizard.flow.phases.resource import WizardResourceLeaf
from palm.patterns.wizard.flow.phases.summary import WizardSummaryLeaf
from palm.patterns.wizard.flow.phases.transform import WizardTransformLeaf

__all__ = [
    "CollectionStepNode",
    "EventEmitter",
    "PhaseKeyedSelectorNode",
    "PhaseTransitionLoopNode",
    "WizardCommitLeaf",
    "WizardCompletionGuardNode",
    "WizardInputLeaf",
    "WizardPhaseContext",
    "WizardResourceLeaf",
    "WizardSequenceNode",
    "WizardStepKindRegistry",
    "WizardSummaryLeaf",
    "WizardTransformLeaf",
    "apply_backtrack",
    "backtrack_notifier",
    "can_backtrack_to",
    "default_wizard_step_registry",
    "phase_transition",
    "provide_wizard_input",
    "register_builtin_wizard_step_kinds",
    "request_backtrack",
]
