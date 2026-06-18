# Wizard Phase Modularization

Wizard execution is organized as behavior-tree **phases** under
`palm/patterns/wizard/phases/`.

## Package layout

| Module | Responsibility |
|--------|----------------|
| `phases/_base.py` | `WizardPhaseContext`, input bridge, prompt helpers |
| `phases/bt.py` | `PhaseKeyedSelectorNode`, `PhaseTransitionLoopNode` |
| `phases/backtrack.py` | `WizardSequenceNode`, completion guard, backtrack policy |
| `phases/input.py` | Interactive input / introduction steps |
| `phases/summary.py` | Answer review and confirmation |
| `phases/commit.py` | Transactional commit via `CommitRegistry` |
| `phases/resource.py` | Core `ResourceLeaf` wrapper |
| `phases/transform.py` | Core `TransformLeaf` wrapper |
| `phases/collection/` | Declarative collection subtree (`tree.py` + phase leaves) |
| `phases/registry.py` | `step_kind` → phase factory registry |

## Tree shape

```
RootNode
  └─ WizardCompletionGuardNode
       └─ WizardSequenceNode
            ├─ WizardInputLeaf | CollectionStepNode | …
            └─ …
```

Collection steps compose a routed subtree:

```
CollectionStepNode
  └─ PhaseTransitionLoopNode
       └─ PhaseKeyedSelectorNode
            ├─ menu
            ├─ select_item
            ├─ field
            └─ remove_confirm
```

Phase leaves signal intra-tick transitions with `PatternStatus.RUNNING` via
`phase_transition()`. The loop re-dispatches when the blackboard phase changes.

## Breaking changes

- Leaf modules at package root (`step_leaf.py`, `collection_leaf.py`, …) are
  removed. Import from `palm.patterns.wizard.phases` instead.
- Legacy aliases (`WizardStepBuildContext`, `WizardStepLeaf`, `WizardCollectionLeaf`)
  are removed. Use `WizardPhaseContext`, `WizardInputLeaf`, `CollectionStepNode`.
- Custom step kinds register factories as `Callable[[WizardPhaseContext], BaseNode]`.

## Register a custom step kind

```python
from palm.core.behavior_tree import ActionNode, PatternStatus
from palm.patterns.wizard import WizardPhaseContext, default_wizard_step_registry

def build_audit(ctx: WizardPhaseContext):
    return ActionNode(ctx.step.slug, action=lambda _s: PatternStatus.SUCCESS)

default_wizard_step_registry().register("audit", build_audit)
```

## `WizardPattern` surface

`WizardPattern` only binds context/state and ticks the root tree. Backtrack,
completion, and per-step logic are handled by phase nodes.