# Palm Agent Guide

MCP resources: `palm://agent/guide` (operator protocol), `palm://agent/skill` (full skill).  
On-disk: `docs/mcp.txt`, `docs/llms.txt` (project context).

## Mental model

Palm = stateful, path-driven workflow engine with interactive wizard support.

- **Flows** — reusable wizards (`todo-builder`, `approval`, …)
- **Sessions** — durable executions (`session_id` ≡ `instance_id`)
- **Assist** — `palm_assist` parametric dispatch (paths, aliases, params)
- **Resources** — read-only `palm://definitions/*`, `palm://instances/{id}/tree`
- **Tools** — write/act: create, input, resume, cancel

## Golden rule

Start with `palm_assist()` unless you have a `session_id` or explicit target flow.

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

## Collection steps

At menu phase: `collection_action: "add"` + `value: "title"`, or `palm_wizard_collection_action`.  
Field edits: `params.edit={item_index: 0, priority: "low"}` (0.21.11).  
Fuzzy menu tokens: `add`, `edit`, `done`, `continue`.