# Branching Flows — Hub Menus and Routing (weak-LLM playbook)

**Load when:** building multi-topic wizards, dialogue-style loops, or revising `coconut-npc`.

**Reference flow:** `coconut-npc` (`palm flow start coconut-npc` · `examples/definitions/coconut_npc.py`)

---

## Pattern: hub-and-spoke

One **hub** step presents a choice menu. Branch steps answer the topic, then **loop back** to the hub or **exit**.

```text
topic (hub) ──route_on_answer──┬→ rumors ──more──┐
                               ├→ trade        │
                               ├→ about        │
                               └→ farewell     │
                                    ↑──────────┘
```

### Hub step (`route_on_answer`)

```json
{
  "slug": "topic",
  "title": "Menu",
  "prompt": "{{ state.mood_line }}\n\nWhat next?",
  "field_type": "choice",
  "choices": ["rumors", "trade", "leave"],
  "params": {
    "route_on_answer": {
      "rumors": "rumors",
      "trade": "trade",
      "leave": "farewell"
    }
  }
}
```

### Branch loop-back

```json
{
  "slug": "rumors",
  "prompt": "…flavor text…",
  "field_type": "choice",
  "choices": ["more", "leave"],
  "params": {
    "route_on_answer": {
      "more": "topic",
      "leave": "farewell"
    }
  }
}
```

### Clean exit (`complete_on`)

```json
{
  "slug": "farewell",
  "prompt": "Safe roads.",
  "field_type": "text",
  "required": false,
  "params": {
    "complete_on": ["exit", "done", "leave", "bye"]
  }
}
```

---

## Transforms between inputs

Use **`step_kind: transform`** for derived state (greetings, lookup tables, formatting):

| Rule | Use |
|------|-----|
| `string_format` | Personalize copy from prior text answer |
| `lookup` | Map choice slug → flavor line |
| `conditional` | If/else on field value |

Flat schema (canonical):

```json
{
  "slug": "mood_line",
  "step_kind": "transform",
  "source_key": "reputation",
  "target_key": "mood_line",
  "rule": "lookup",
  "options": { "table": { "friend": "…" }, "default": "…" }
}
```

---

## Prompt interpolation (0.27.1+)

Reference prior answers in prompts with **`{{ state.key }}`** (same binding as resource params):

```json
"prompt": "{{ state.mood_line }}\n\nWell then. What'll it be?"
```

Keys resolve from wizard **answers** (e.g. `mood_line`, `player_name`).

---

## MCP workflow

```text
palm_design_propose_flow(body={...})     # or base_flow_id to revise
palm_design_impact(proposal_id)
palm_design_commit(proposal_id)
palm_flows_create_session(flow_id="coconut-npc")
```

Drive with `palm_flows_session(..., format="assistant")` → `palm_flows_session_input` after every step.

---

## Anti-patterns

- Linear-only steps with no hub — hard to add topics later.
- Forgetting `"more": "topic"` loop-back — conversation cannot continue.
- Auto-confirm at farewell — use `complete_on`, wait for user token.
- JSON blobs for choice answers — send slug strings (`rumors`, `leave`).