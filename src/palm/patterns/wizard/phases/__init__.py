"""
Wizard phases — BT-native step implementations.

Package layout::

    phases/
      _base.py       shared context, input bridge, prompt helpers
      bt.py          reusable phase routing composites
      backtrack.py   sequence navigation + completion guard
      input.py       interactive input/introduction steps
      summary.py     answer review step
      commit.py      transactional commit step
      resource.py    ResourceLeaf wrapper step
      transform.py   TransformLeaf wrapper step
      collection/    multi-phase collection subtree
      registry.py    step_kind → phase factory registry

Each wizard step kind maps to a dedicated phase module that builds behavior-tree
nodes. ``WizardPattern`` itself only binds context and ticks the root tree.
"""

from palm.patterns.wizard.phases._base import (
    EventEmitter,
    WizardPhaseContext,
    provide_wizard_input,
)
from palm.patterns.wizard.phases.backtrack import (
    WizardCompletionGuardNode,
    WizardSequenceNode,
    apply_backtrack,
    backtrack_notifier,
    can_backtrack_to,
    request_backtrack,
)
from palm.patterns.wizard.phases.bt import (
    PhaseKeyedSelectorNode,
    PhaseTransitionLoopNode,
    phase_transition,
)
from palm.patterns.wizard.phases.collection.step import CollectionStepNode
from palm.patterns.wizard.phases.commit import WizardCommitLeaf
from palm.patterns.wizard.phases.input import WizardInputLeaf
from palm.patterns.wizard.phases.registry import (
    WizardStepKindRegistry,
    default_wizard_step_registry,
    register_builtin_wizard_step_kinds,
)
from palm.patterns.wizard.phases.resource import WizardResourceLeaf
from palm.patterns.wizard.phases.summary import WizardSummaryLeaf
from palm.patterns.wizard.phases.transform import WizardTransformLeaf

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