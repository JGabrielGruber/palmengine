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