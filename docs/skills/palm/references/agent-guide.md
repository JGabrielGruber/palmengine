# Palm Agent Guide

MCP resources: `palm://agent/guide` (operator protocol), `palm://agent/skill` (full skill).  
On-disk: `docs/mcp.txt`, `docs/llms.txt` (project context).

## Mental model

Palm = stateful, path-driven workflow engine with interactive wizard support.

- **Flows** — reusable wizards (`todo-builder`, `approval`, custom flows you publish, …)
- **Sessions** — durable executions (`session_id` ≡ `instance_id`)
- **Assist** — `palm_assist` parametric dispatch (paths, aliases, params)
- **Design (0.25+)** — safe catalog writes via `palm_design_*` (propose → impact → commit)
- **Resources** — read-only `palm://definitions/*`, `palm://instances/{id}/tree`, skill references
- **Tools** — write/act: design, create session, input, resume, cancel

## Golden rules

| Task | Start here |
|------|------------|
| Run an existing flow | `palm_assist()` unless you have `session_id` or explicit `flow_id` |
| Create or change a flow definition | `palm://agent/references/design-flows` + `palm_design_*` — **not** repo files or `palm_definitions_*` writes |

## View modes

| Mode | Where | Shape |
|------|-------|-------|
| Assistant | assist paths, opt-in flows | `question`, `choices`, `hint`, `actions` |
| Powertool | `palm_flows_*` default | `operator_hint`, `step_kind` |

## Typical session (0.21.7+)

```
palm_assist()                                          → operator-entry
palm_assist(params={"session_id": id, "value": "yes"}) → continue assist
palm_assist(alias="operator-entry/handoff", params={"session_id": id})
palm_assist(path=["flows", "todo-builder", "create"])  → business session
palm_assist(params={session_id, flow_id, value})       → flows input (0.21.10)
```

## Design loop (create or improve flows)

Always run **all steps in order**. Save `proposal_id` from step 1.

```
palm_design_propose_flow(body={...})              # new flow, or base_flow_id="foo-bar" to revise
palm_design_impact(proposal_id="prop-...")
palm_design_commit(proposal_id="prop-...")
palm_flows_describe(flow_id="my-flow")          # verify revision published
```

Full weak-LLM playbook (body shape, choice steps, `foo-bar` walkthrough): **`palm://agent/references/design-flows`**.

## Collection steps

At menu phase: `collection_action: "add"` + `value: "title"`, or `palm_wizard_collection_action`.  
Field edits: `params.edit={item_index: 0, priority: "low"}` (0.21.11).  
Fuzzy menu tokens: `add`, `edit`, `done`, `continue`.

## Choice and summary steps (running flows)

| Step type | Send |
|-----------|------|
| Text | `input="plain string"` |
| Choice | `input="beta"` or `input="2"` from assistant `choices` |
| Summary (`include_summary`) | `input="yes"` only when user explicitly confirms — never auto-confirm on inspect |

Re-inspect with `palm_flows_session(..., format="assistant")` after **every** input.