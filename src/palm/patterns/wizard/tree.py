"""
Build behavior-tree structures for a configured wizard.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.behavior_tree import BaseNode, RootNode, SequenceNode
from palm.core.resource import ResourceEngine

if TYPE_CHECKING:
    from palm.core.context import ContextEngine
from palm.patterns.wizard.action_leaf import WizardActionLeaf
from palm.patterns.wizard.collection_leaf import WizardCollectionLeaf
from palm.patterns.wizard.commit_leaf import WizardCommitLeaf
from palm.patterns.wizard.config import WizardConfig
from palm.patterns.wizard.handler import CommitRegistry
from palm.patterns.wizard.step_leaf import EventEmitter, WizardStepLeaf
from palm.patterns.wizard.summary_leaf import WizardSummaryLeaf
from palm.patterns.wizard.resource_leaf import WizardResourceLeaf
from palm.patterns.wizard.transform_leaf import WizardTransformLeaf


def build_wizard_tree(
    wizard_name: str,
    config: WizardConfig,
    emit: EventEmitter | None = None,
    *,
    commit_registry: CommitRegistry | None = None,
    resource_engine: ResourceEngine | None = None,
    context_engine: ContextEngine | None = None,
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
                    context_engine=context_engine,
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
                    context_engine=context_engine,
                )
            )
        elif step.step_kind == "collection":
            leaves.append(
                WizardCollectionLeaf(
                    step,
                    wizard_name=wizard_name,
                    step_index=idx,
                    emit=emit,
                    context_engine=context_engine,
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
                    context_engine=context_engine,
                )
            )
        elif step.step_kind == "resource":
            leaves.append(
                WizardResourceLeaf(
                    step,
                    wizard_name=wizard_name,
                    step_index=idx,
                    resource_engine=resource_engine,
                    emit=emit,
                    context_engine=context_engine,
                )
            )
        elif step.step_kind == "transform":
            leaves.append(
                WizardTransformLeaf(
                    step,
                    wizard_name=wizard_name,
                    step_index=idx,
                    emit=emit,
                    context_engine=context_engine,
                    resource_engine=resource_engine,
                )
            )
        else:
            leaves.append(
                WizardStepLeaf(
                    step,
                    wizard_name=wizard_name,
                    step_index=idx,
                    emit=emit,
                    context_engine=context_engine,
                )
            )

    sequence = SequenceNode(f"{wizard_name}_sequence", children=leaves)
    root = RootNode(f"{wizard_name}_root", child=sequence)
    return root, sequence
