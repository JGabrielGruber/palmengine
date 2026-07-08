# Common Palm Flows

## Todo Builder

- **Start**: `palm_assist()` → Todo Builder, or `palm_assist(path=["flows","todo-builder","create"])`
- **Steps**: intro → collection (add/edit/remove) → summary → commit
- **Collection**: `palm_assist(params={session_id, flow_id, collection_action: "add", value: "title"})`

## Approval

- **Start**: `palm_assist(path=["flows","approval","create"])`
- **Steps**: title → amount → approver → justification → summary → commit

## Onboard / schema-onboard

- **Start**: `palm_assist(path=["flows","onboard","create"])`
- Good for testing wizard mechanics.

## Coconut NPC (`coconut-npc`) — branching reference + KV resources

**Start (0.30.6+, preferred):**

```text
palm_assist(params={flow_id: "coconut-npc"})
  → first question (assistant format)
palm_assist(params={session_id, flow_id: "coconut-npc", value: "YourName"})
```

Or pick **coconut-npc** from operator-entry. Resources `load-coconut-player` / `save-coconut-player` auto-run between steps; if stuck: **Resume resource step** or `palm_system_doctor`.

Hub-and-spoke wizard: transforms + `route_on_answer` + loop-back to topic menu. Regression profile for compositional workflows ([VISION-0.27.md](../../../../VISION-0.27.md)).

```bash
palm flow start coconut-npc
# or palm_flows_create_session(flow_id="coconut-npc")
```

## Custom flows (design + run)

When the user asks to **create or improve** a flow (not run a built-in one):

1. Read **`palm://agent/references/design-flows`** (step-by-step for weak models).
2. Propose → impact → commit with `palm_design_*`.
3. Run with `palm_flows_create_session(flow_id="<slug>")`.

**Worked example:** `foo-bar` — two text steps, then revision 2 with choice step + summary. Full recipe in design-flows §F.

**Name rule:** flow `name` must be a slug (`foo-bar`, not `foo bar`).

## Migrate instance demo (0.24.3+)

- **Prerequisite**: session on `migrate-demo-source` (revision 1) — `palm flow start migrate-demo-source`
- **Operator wizard**: `palm flow start migrate-instance-demo` — confirm → dry-run → apply
- **API**: `palm_definitions_analyze_impact` → `palm_definitions_migrate_instance(dry_run=True)` → apply
- See [MIGRATION-0.24.md](../../../../MIGRATION-0.24.md)

## General pattern (running any flow)

1. Create session (operator-entry or `flows/<name>/create` or `palm_flows_create_session`)
2. Inspect with `format=assistant`
3. Send `value` / `input` for each step (plain strings; choice slugs; `yes` at summary only if user confirms)
4. Re-inspect after every step
5. Confirm at summary/commit (`input="yes"`)

## Discovery

- `palm_flows_list()` — runnable flows (committed definitions only)
- `palm://definitions/flows` — catalog with step slugs
- `palm://assist/routes` — full command-path + alias catalog
- `palm://agent/references/design-flows` — create/improve flows playbook