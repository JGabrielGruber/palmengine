"""Declarative behavior-tree construction for wizard branch step subtrees."""

from __future__ import annotations

from palm.core.behavior_tree import BaseNode, ConditionNode, SelectorNode, SequenceNode
from palm.patterns.wizard.bindings.definitions.config import WizardStepConfig
from palm.patterns.wizard.flow.branch.predicate import evaluate_branch_predicate
from palm.patterns.wizard.flow.phases._base import WizardPhaseContext


def build_branch_subtree(
    ctx: WizardPhaseContext,
    *,
    registry: object,
) -> BaseNode:
    """
    Return a selector subtree for one branch wizard step.

    Tree shape::

        SelectorNode
          ├─ SequenceNode (then)
          │    ├─ ConditionNode(when)
          │    └─ nested phase leaves …
          └─ SequenceNode (else)
               └─ nested phase leaves …
    """
    step = ctx.step
    when = dict(step.when or {})
    then_steps = step.then_steps
    else_steps = step.else_steps

    then_children = [
        ConditionNode(
            f"{step.slug}_when",
            predicate=lambda state, clause=when: evaluate_branch_predicate(state, clause),
        ),
        *[
            _build_nested_phase(ctx, nested, registry=registry)
            for nested in then_steps
        ],
    ]
    else_children = [
        _build_nested_phase(ctx, nested, registry=registry) for nested in else_steps
    ]

    return SelectorNode(
        f"{step.slug}_selector",
        children=[
            SequenceNode(f"{step.slug}_then", children=then_children),
            SequenceNode(f"{step.slug}_else", children=else_children),
        ],
    )


def _build_nested_phase(
    parent_ctx: WizardPhaseContext,
    step: WizardStepConfig,
    *,
    registry: object,
) -> BaseNode:
    nested_ctx = WizardPhaseContext(
        wizard_name=parent_ctx.wizard_name,
        step_index=parent_ctx.step_index,
        step=step,
        emit=parent_ctx.emit,
        commit_registry=parent_ctx.commit_registry,
        resource_engine=parent_ctx.resource_engine,
        context_engine=parent_ctx.context_engine,
    )
    build = getattr(registry, "build", None)
    if not callable(build):
        raise TypeError("branch subtree requires a step registry with build()")
    return build(nested_ctx)