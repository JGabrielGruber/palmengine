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

## Migrate instance demo (0.24.3+)

- **Prerequisite**: session on `migrate-demo-source` (revision 1) — `palm flow start migrate-demo-source`
- **Operator wizard**: `palm flow start migrate-instance-demo` — confirm → dry-run → apply
- **API**: `palm_definitions_analyze_impact` → `palm_definitions_migrate_instance(dry_run=True)` → apply
- See [MIGRATION-0.24.md](../../../../MIGRATION-0.24.md)

## General pattern

1. Create session (operator-entry or `flows/<name>/create`)
2. Inspect with `format=assistant`
3. Send `value` / `input` for each step
4. Re-inspect after every step
5. Confirm at summary/commit (`input="yes"`)

## Discovery

- `palm_flows_list()` — runnable flows
- `palm://definitions/flows` — catalog with step slugs
- `palm://assist/routes` — full command-path + alias catalog