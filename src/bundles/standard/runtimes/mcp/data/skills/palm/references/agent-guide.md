# Palm Agent Guide

MCP resources: `palm://agent/guide` (operator protocol), `palm://agent/skill` (full skill).  
On-disk: `docs/mcp.txt`, `docs/llms.txt` (project context).

## Mental model

Palm = stateful, path-driven workflow engine with interactive wizard support.

- **Flows** — reusable wizards (`todo-builder`, `approval`, custom flows you publish, …)
- **System session** — outside subject (`session_id` = `sess-…`); may own many instances (0.58)
- **Instance** — one run / continue handle (`instance_id`); product paths use segment `instance`
- **BoundSurface / SessionService** — product bind door (not a second resume path)
- **Assist** — `palm_assist` parametric dispatch (paths, aliases, params)
- **Design (0.25+)** — prefer `palm_design_publish_flow` or `palm_assist(params={body})`. Alternate: propose → impact → commit
- **Resources** — read-only `palm://definitions/*`, `palm://instances/{id}/tree`, skill references
- **Tools** — write/act: design, create, input, resume, cancel

**Do not** treat `session_id` ≡ `instance_id`. Detail: `session-management.md`.

## Golden rules

| Task | Start here |
|------|------------|
| Run an existing flow | `palm_assist()` unless you have continue `instance_id` or explicit `flow_id` |
| Create or change a flow definition | `palm://agent/references/design-flows` + one-shot publish — **not** repo files or `palm_definitions_*` writes |

## View modes

| Mode | Where | Shape |
|------|-------|-------|
| Assistant | assist paths, opt-in flows | `question`, `choices`, `hint`, `actions` |
| Powertool | `palm_flows_*` default | `operator_hint`, `step_kind` |

## Typical walk (0.21.7+ · vocabulary 0.58)

```
palm_assist()                                             → operator-entry
palm_assist(params={instance_id: id, value: "yes"})       → continue (prefer instance_id)
palm_assist(alias="operator-entry/handoff", params={instance_id: id})
palm_assist(path=["flows", "todo-builder", "create"])     → start business instance
palm_assist(params={instance_id, flow_id, value})         → flows input
```

Legacy: param name `session_id` may still carry the continue handle when the value is not `sess-…`.

## Design loop (create or improve flows)

Prefer one-shot, then `palm_flows_describe`. Alternate (debug only): propose → impact → commit.

```
palm_design_publish_flow(body={...})              # or palm_assist(params={body}); base_flow_id to revise
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

Re-inspect with `palm_flows_session(..., format="assistant")` (continue id) after **every** input.