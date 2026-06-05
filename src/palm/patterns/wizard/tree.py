"""
Build behavior-tree structures for a configured wizard.
"""

from __future__ import annotations

from palm.core.behavior_tree import BaseNode, RootNode, SequenceNode
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.action_leaf import WizardActionLeaf
from palm.patterns.wizard.commit import CommitRegistry
from palm.patterns.wizard.commit_leaf import WizardCommitLeaf
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.step_leaf import EventEmitter, WizardStepLeaf
from palm.patterns.wizard.summary_leaf import WizardSummaryLeaf


def build_wizard_tree(
    wizard_name: str,
    config: WizardConfig,
    emit: EventEmitter | None = None,
    *,
    commit_registry: CommitRegistry | None = None,
    resource_engine: ResourceEngine | None = None,
) -> tuple[RootNode, SequenceNode]:
    """Return ``(root, sequence)`` for the given wizard configuration."""
    registry = commit_registry
    leaves: list[BaseNode] = []

    for idx, step in enumerate(config.iter_tree_steps()):
        if step.step_kind == "summary":
            leaves.append(
                WizardSummaryLeaf(
                    step,
                    wizard_name=wizard_name,
                    step_index=idx,
                    emit=emit,
                )
            )
        elif step.step_kind == "commit":
            hook = step.commit_hook or config.commit_hook
            if not hook or registry is None:
                raise ValueError(
                    f"Commit step {step.slug!r} requires commit_hook and CommitRegistry"
                )
            leaves.append(
                WizardCommitLeaf(
                    step,
                    wizard_name=wizard_name,
                    step_index=idx,
                    hook_name=hook,
                    commit_registry=registry,
                    resource_engine=resource_engine,
                    emit=emit,
                )
            )
        elif step.step_kind == "action":
            leaves.append(
                WizardActionLeaf(
                    step,
                    wizard_name=wizard_name,
                    step_index=idx,
                    resource_engine=resource_engine,
                    emit=emit,
                )
            )
        else:
            leaves.append(
                WizardStepLeaf(
                    step,
                    wizard_name=wizard_name,
                    step_index=idx,
                    emit=emit,
                )
            )

    sequence = SequenceNode(f"{wizard_name}_sequence", children=leaves)
    root = RootNode(f"{wizard_name}_root", child=sequence)
    return root, sequence
