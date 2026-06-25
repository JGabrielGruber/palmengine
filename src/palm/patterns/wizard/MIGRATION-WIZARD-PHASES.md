# Wizard Phase Modularization

Wizard execution is organized as behavior-tree **phases** under
`palm/patterns/wizard/phases/`.

## Package layout

| Module | Responsibility |
|--------|----------------|
| `app.py` | Manifest — Palm layer dependencies and registry hooks |
| `bindings/behavior_tree/` | Tree assembly, BT composites, sequence/backtrack |
| `bindings/context/` | Blackboard keys, scopes, step state |
| `bindings/events/` | Event types and leaf emission helpers |
| `bindings/resource/` | Child-job wait coordination |
| `bindings/instances/` | Persistence, resume, submission metadata |
| `bindings/definitions/` | Flow options, config, builder |
| `bindings/compensation/` | Commit handlers |
| `flow/phases/` | Interactive step leaves (input, summary, commit, resource, transform) |
| `flow/collection/` | Collection config, state, and `phases/` subtree |
| `flow/extensions/` | `step_kind` → phase factory registry |
| `flow/validation.py` | Step validation rules and feedback |
| `bindings/bridges.py` | Runtime hooks on `patterns/_registry` (interactive, child-wait, read-model) |
| `bindings/read_model.py` | REST wizard view assembly (`build_wizard_view`) |
| `bindings/cqrs/` | Wizard-owned CQRS commands, queries, projection, and handlers |
| `app.py` | `WizardApp(PatternApp)` — manifest, `ready()` registry wiring |

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

## Phase 3 — PatternApp + common cleanup

- `PatternApp` base lives in `palm.common.patterns.app`; each pattern subpackage
  provides an app stub and `WizardApp` registers bridges, projection factory, and
  CQRS contributor hooks in `ready()`.
- Wizard CQRS types and `WizardProgressProjection` moved to
  `palm.patterns.wizard.bindings.cqrs.*`. Import from there (not `palm.common`).
- Generic dispatchers in common: `interactive_runtime.py`, `child_wait.py`,
  `patterns/pattern_read_model.py`. No `wizard_*` modules remain in `palm.common`.
- Durable instance field renamed: `wizard_step_slug` → `current_step_slug`
  (read compat accepts legacy `wizard_step_slug` in persisted JSON).

## Breaking changes

- Leaf modules at package root (`step_leaf.py`, `collection_leaf.py`, …) are
  removed. Import from `palm.patterns.wizard.flow.phases` (or the
  `palm.patterns.wizard.phases` compatibility shim).
- Internal modules moved under `bindings/` (Palm layer integration) and
  `flow/` (wizard orchestration). Public `palm.patterns.wizard` exports are
  unchanged.
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