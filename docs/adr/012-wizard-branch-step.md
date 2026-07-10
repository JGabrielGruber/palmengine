# ADR-012: Wizard Branch Step (`step_kind: branch`)

## Status

**Accepted** — July 2026 (Tier 1 — state-driven wizard branching)

## Context

The **`coconut-npc`** reference flow needs state-driven control flow: returning travelers
(load `visit_count > 0` from KV) must skip the `reputation` input while first-time visitors
run it. Prior work used example-local custom transforms that set `WizardKeys.JUMP_TO_STEP`,
which leaks wizard internals into flow definitions and bypasses the behavior-tree model.

Palm already embeds **composite subtrees** inside the linear wizard spine (`CollectionStepNode`
uses `PhaseKeyedSelectorNode` + `PhaseTransitionLoopNode`). Core BT primitives include
`ConditionNode` and `SelectorNode`. Hub menus use `route_on_answer` on **input** steps
(answer-driven jumps), not state-driven guards.

Cross-job composition (`palm` provider `submit_flow`) remains the path for separate reusable
sub-wizards ([ADR-001](001-compositional-power-resources.md)); coconut’s need is an
**in-tree conditional path**, not a child job.

## Decision

1. **Add `step_kind: branch`** — a wizard phase registered in `flow/extensions/registry.py`,
   following the `CollectionStepNode` precedent (one slot in `WizardSequenceNode` wraps a subtree).

2. **Declarative shape**

   ```json
   {
     "slug": "reputation_gate",
     "step_kind": "branch",
     "title": "Reputation routing",
     "when": { "field": "is_returning", "is_truthy": true },
     "then": [ { "slug": "restore_mood", "step_kind": "transform", "rule": "lookup", … } ],
     "else": [ { "slug": "reputation", "title": "Coconut", "field_type": "choice", … } ]
   }
   ```

3. **BT shape** (truth-seeking, no imperative jump keys for branch routing)

   ```text
   BranchStepNode (DecoratorNode)
     └─ SelectorNode
          ├─ SequenceNode (then arm)
          │    ├─ ConditionNode(when predicate)
          │    └─ … nested phase leaves …
          └─ SequenceNode (else arm)
               └─ … nested phase leaves …
   ```

   - Predicate vocabulary matches the built-in `conditional` transform
     (`field`, `equals`, `gt`, `gte`, `is_truthy`, `exists`, …).
   - Predicate reads wizard **answers** first, then root blackboard keys.
   - When the `then` arm’s condition fails, `SelectorNode` falls through to `else`.

4. **Slug policy**
   - Top-level `WizardConfig.iter_tree_steps()` lists only spine steps (branch is one entry).
   - `iter_all_step_slugs()` flattens nested `then`/`else` steps for uniqueness validation.
   - During execution, `CURRENT_STEP` reflects the active nested leaf slug (same as collection phases).

5. **Tier 1 scope**
   - Nested steps: `input`, `transform`, `resource` (no nested `branch`, `collection`, or `commit`).
   - Design contributor validates `when`, non-empty `then`/`else` lists, and global slug uniqueness.
   - Coconut refactored to KV resources + built-in transforms + `branch`; example custom transforms removed.

6. **Deferred (Tier 2+)**
   - `step_kind: flow` (inline child wizard without child job).
   - `params.skip_when` on individual steps.
   - Backtrack into/out of branch arms (inherits parent `allow_backtrack`; no special policy in 0.30).

## Consequences

### Positive

- State-driven branching without custom transforms or `JUMP_TO_STEP` hacks.
- Reuses core `ConditionNode` + `SelectorNode`; aligns with collection’s composite-step pattern.
- Predicate DSL shared conceptually with `conditional` transform (data vs control separation).

### Negative

- Nested steps are not in top-level `step_index` / `index_of()` — hub `route_on_answer` targets
  top-level slugs only.
- Design and MCP `step_slugs` must flatten branch arms for discoverability.

## Links

- [ADR-001](001-compositional-power-resources.md) — compositional sub-flows via `palm` provider
- [ADR-011](011-local-document-resources.md) — coconut KV persistence
- `examples/definitions/coconut/npc.py` — reference consumer