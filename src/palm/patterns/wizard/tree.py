"""
Build behavior-tree structures for a configured wizard.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.behavior_tree import RootNode
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.completion_guard import WizardCompletionGuardNode
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.handler import CommitRegistry
from palm.patterns.wizard.step_leaf import EventEmitter
from palm.patterns.wizard.step_registry import (
    WizardStepBuildContext,
    WizardStepKindRegistry,
    default_wizard_step_registry,
)
from palm.patterns.wizard.wizard_sequence import BacktrackNotifier, WizardSequenceNode

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

    The tree shape is::

        RootNode
          └─ WizardCompletionGuardNode
               └─ WizardSequenceNode
                    ├─ step leaf …
                    └─ step leaf …

    Custom step kinds can be supplied via ``step_registry`` (defaults to the
    global built-in registry).
    """
    registry = step_registry or default_wizard_step_registry()
    on_backtrack = _backtrack_notifier(emit, wizard_name) if emit is not None else None

    leaves = [
        registry.build(
            WizardStepBuildContext(
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
    )
    root = RootNode(f"{wizard_name}_root", child=guard)
    return root, sequence


def _backtrack_notifier(
    emit: EventEmitter,
    wizard_name: str,
) -> BacktrackNotifier:
    from palm.core.context import BaseState
    from palm.patterns.wizard.keys import WizardKeys

    def notify(index: int, state: BaseState, slug: str, from_step: object) -> None:
        payload = {
            "wizard": wizard_name,
            "step_index": index,
            "slug": slug,
            "from_step": from_step,
            "to_slug": slug,
        }
        emit(WizardEventType.BACKTRACK, payload)
        emit(WizardEventType.BACKTRACK_EXECUTED, payload)

    return notify