"""
Build behavior-tree structures for a configured wizard.
"""

from __future__ import annotations

from palm.core.behavior_tree import BaseNode, RootNode, SequenceNode
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.step_leaf import EventEmitter, WizardStepLeaf


def build_wizard_tree(
    wizard_name: str,
    config: WizardConfig,
    emit: EventEmitter | None = None,
) -> tuple[RootNode, SequenceNode]:
    """Return ``(root, sequence)`` for the given wizard configuration."""
    leaves: list[BaseNode] = [
        WizardStepLeaf(
            step,
            wizard_name=wizard_name,
            step_index=idx,
            emit=emit,
        )
        for idx, step in enumerate(config.steps)
    ]
    sequence = SequenceNode(f"{wizard_name}_sequence", children=leaves)
    root = RootNode(f"{wizard_name}_root", child=sequence)
    return root, sequence