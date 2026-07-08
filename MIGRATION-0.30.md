# Migration Guide — Palm 0.30 (Assist design entry)

**Scope:** Assist discovery of Design Service (0.30.0–0.30.3).  
**Vision:** [docs/VISION-0.30.md](docs/VISION-0.30.md)

---

## Who is affected

| Audience | Impact |
|----------|--------|
| Agents using `palm_assist` / operator-entry | New intents and actions for create/improve flow |
| Clients that parse `AssistService.handoff()` strictly | **`kind: design` added (0.30.3)** |
| Integrators with custom assist metadata | Optional `design_handoff_intents`, `create_params_from_answers` |

---

## Breaking / behavioral notes

### Handoff `kind: design` (0.30.3)

Previously, design intents returned:

```json
{ "handoff": { "kind": "none", "operator_hint": "…design tools…" } }
```

With `design_handoff_intents` on the scenario (operator-entry, design-entry):

```json
{
  "handoff": {
    "kind": "design",
    "flow_id": null,
    "session_id": null,
    "create_params": {},
    "intent": "create-flow",
    "design_action": "propose_flow",
    "suggested_name": "optional-from-name_or_base",
    "operator_hint": "Use palm_design_propose_flow…"
  }
}
```

| Field | Meaning |
|-------|---------|
| `design_action` | `propose_flow` or `propose_resource` |
| `base_flow_id` | Set for `improve-flow` when `name_or_base` answered |
| `suggested_name` | Set for `create-flow` / `propose-resource` when `name_or_base` answered |
| `operator_hint` | Always present — primary agent instruction |

**Client rule (required):** Treat **unknown** `kind` values the same as `none` and **always** read `operator_hint`. Do not fail closed if `kind` is not `flow` | `none`.

Strict clients that only branch on `kind == "flow"` will no longer match design handoffs (same as `none` before) — they should use `operator_hint` / `design_action`.

### Operator-entry choices (0.30.1+)

New choice slugs: `create-flow`, `improve-flow` (plus demos and `inspect-only`).

### design-entry scenario (0.30.2+)

Alias `design-entry/start` → assist scenario shell. **Does not** write the catalog; agents still call `palm_design_*`.

---

## 0.30.4 — One-shot publish (weak-LLM)

Preferred agent path is no longer three tools:

| Before | After |
|--------|--------|
| `propose` → `impact` → `commit` | **`palm_design_publish_flow(body=…)`** (or `publish_resource`) |
| Multiple design CTAs | Single primary CTA: **Publish … (one call)** |

Step-by-step tools remain for power users. `design_action` on handoff is `publish_flow` / `publish_resource`.

## 0.30.5 — Shorter assist design path

| Change | Effect |
|--------|--------|
| operator-entry `create-flow` / `improve-flow` | Jump to `__end__` — **no summary yes** |
| design-entry | `include_summary: false`; ends after `name_or_base` |
| `palm_assist(params={body: {…}})` | Infers alias **`design/publish`** (no separate tool required) |

Agents that always sent summary `yes` after create-flow can stop; session is already complete with publish CTAs.

## 0.30.6 — Flow driving + resources via palm_assist

| Change | Effect |
|--------|--------|
| Flows via `palm_assist` | **Assistant** format by default (question/choices), not powertool |
| `palm_assist(params={flow_id})` | Starts that flow (create) and re-inspects first turn |
| operator-entry choices | Adds **`coconut-npc`** (KV resource demo) and **`propose-resource`** |
| Resource step failure | Assistant actions: resume, doctor, publish resource |

`palm_flows_*` tools remain powertool-default when called directly.

## Unchanged

- Bare `palm_assist()` still starts **operator-entry** (not design-entry).
- Multi-step Design APIs remain available.
- Business flow handoffs (`kind: flow`) for todo-builder / compositional-parent unchanged.
- `kind: process` remains deferred.

---

## Upgrade checklist

1. Update agent prompts / MCP skill to load design-flows and accept `kind: design`.
2. If you parse handoff JSON, add a branch for `design` or fall through to `operator_hint`.
3. Restart in-process `palm-mcp` after upgrade so example scenarios reload.
4. Optional: set `design_handoff_intents` on custom assist flows to opt into typed design handoff.
