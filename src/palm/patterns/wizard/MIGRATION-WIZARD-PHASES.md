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

## Explorer + REST (0.13)

Operators can run the same collection phases through **Palm Explorer** without
typing menu strings:

| Explorer action | Wizard input equivalent |
|-----------------|-------------------------|
| Add New | `"Add a new item"` |
| Edit item N | `"Edit an item"` + item selection |
| Remove item N | `"Remove an item"` + item selection |
| Continue to summary | `"Continue to summary"` |
| Field value | per-field `provide_input` |
| Remove confirm | `yes` / `no` |

Explorer posts `collection_action` forms to `/explorer/instances/{id}/input`.
REST clients use `/v1/wizards/{id}/input` with `{"value": ...}`.

The `prompt` block on `GET /v1/wizards/{id}` includes `collection_phase`,
`collection_items`, `collection_draft`, `item_fields`, and related metadata
from live job inspection — Explorer renders phase-specific UI from this payload.

See [EXPLORER-WIZARD.md](../../../../EXPLORER-WIZARD.md) (repo root).