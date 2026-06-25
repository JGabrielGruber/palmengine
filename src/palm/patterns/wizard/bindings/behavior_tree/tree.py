"""
Build behavior-tree structures for a configured wizard.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.behavior_tree import RootNode
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.bindings.definitions.config import WizardConfig
from palm.patterns.wizard.bindings.compensation.handler import CommitRegistry
from palm.patterns.wizard.flow.phases._base import EventEmitter, WizardPhaseContext
from palm.patterns.wizard.bindings.behavior_tree.backtrack import (
    WizardCompletionGuardNode,
    WizardSequenceNode,
    backtrack_notifier,
)
from palm.patterns.wizard.flow.extensions.registry import (
    WizardStepKindRegistry,
    default_wizard_step_registry,
)

if TYPE_CHECKING:
    from palm.core.context import ContextEngine


def build_wizard_tree(
    wizard_name: str,
    config: WizardConfig,
    emit: EventEmitter | None = None,
    *,
    commit_registry: CommitRegistry | None = None,
    resource_engine: ResourceEngine | None = None,
    context_engine: ContextEngine | None = None,
    step_registry: WizardStepKindRegistry | None = None,
) -> tuple[RootNode, WizardSequenceNode]:
    """
    Return ``(root, sequence)`` for the given wizard configuration.

    Tree shape::

        RootNode
          └─ WizardCompletionGuardNode
               └─ WizardSequenceNode
                    ├─ phase node …
                    └─ phase node …
    """
    registry = step_registry or default_wizard_step_registry()
    on_backtrack = backtrack_notifier(emit, wizard_name) if emit is not None else None

    leaves = [
        registry.build(
            WizardPhaseContext(
                wizard_name=wizard_name,
                step_index=idx,
                step=step,
                emit=emit,
                commit_registry=commit_registry,
                resource_engine=resource_engine,
                context_engine=context_engine,
            )
        )
        for idx, step in enumerate(config.iter_tree_steps())
    ]

    sequence = WizardSequenceNode(
        f"{wizard_name}_sequence",
        config=config,
        children=leaves,
        on_backtrack=on_backtrack,
    )
    guard = WizardCompletionGuardNode(
        f"{wizard_name}_completion",
        child=sequence,
        config=config,
        emit=emit,
        wizard_name=wizard_name,
    )
    root = RootNode(f"{wizard_name}_root", child=guard)
    return root, sequence