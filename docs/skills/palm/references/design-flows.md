# Design Flows — Create, Improve, and Run (weak-LLM playbook)

**Load when:** user asks to create, change, or publish a flow definition — or after reading `palm://agent/guide` §15.

**Golden rule:** use **`palm_design_*`** tools for catalog writes. Do **not** use `palm_definitions_*` create/update unless an integrator doc explicitly requires it.

---

## A. Create a new wizard flow (copy this loop)

Always run **all four steps in order**. Save `proposal_id` from step 1.

```text
1. palm_design_propose_flow(body={...})
2. palm_design_impact(proposal_id="prop-...")
3. palm_design_commit(proposal_id="prop-...")
4. palm_flows_describe(flow_id="my-flow")   ← verify revision published
```

**Optional:** `palm_design_validate(proposal_id)` if propose did not return `"valid": true`.

### Minimal `body` (wizard)

```json
{
  "name": "my-flow",
  "pattern": "wizard",
  "options": {
    "include_summary": true,
    "allow_backtrack": true,
    "steps": [
      {
        "slug": "foo",
        "title": "Foo",
        "prompt": "What is your foo?",
        "validation": [{"rule": "min_length", "params": {"min": 2}}]
      },
      {
        "slug": "bar",
        "title": "Bar mode",
        "prompt": "Pick a bar style",
        "field_type": "choice",
        "choices": ["alpha", "beta", "gamma"]
      }
    ]
  }
}
```

### Transform steps (flat schema — canonical)

```json
{
  "slug": "format_greeting",
  "step_kind": "transform",
  "source_key": "player_name",
  "target_key": "greeting_line",
  "rule": "string_format",
  "options": { "template": "Ah, {value} — …" }
}
```

Nested `"transform": { ... }` is normalized at validate time but **prefer flat** fields.

### Prompt interpolation (0.27.1+)

Use `{{ state.key }}` in step `prompt` / `title` — resolves from wizard answers:

```json
"prompt": "{{ state.mood_line }}\n\nWhat'll it be?"
```

### Resource proposals (0.27.2+)

```text
palm_design_propose_resource(body={name, provider, action, resource_id, ...})
palm_design_impact(proposal_id)
palm_design_commit(proposal_id)
```

Impact lists flows referencing the `resource_ref`. See `coconut-npc` + `palm://agent/references/branching-flows`.

### Name rules (common mistakes)

| Wrong | Right |
|-------|-------|
| `"name": "foo bar"` (spaces) | `"name": "foo-bar"` (slug) |
| Missing `slug` on a step | Every step needs `slug`, `title`, `prompt` |
| `field_type: choice` without `choices` | Always include `choices: [...]` |

---

## B. Improve an existing flow (new revision)

Same loop as §A, but pass **`base_flow_id`** on propose:

```text
palm_design_propose_flow(
  base_flow_id="foo-bar",
  body={ "name": "foo-bar", "pattern": "wizard", "options": { ... } }
)
```

Then impact → commit. Revision increments (`revision: 2`, `3`, …).

**Impact note:** finished instances stay on their old revision (`snapshot_only`) — that is normal. New sessions use the latest revision.

---

## C. Run a flow after publish

Design tools **define** flows. **Running** uses flow session tools:

```text
1. palm_flows_create_session(flow_id="foo-bar")
   → save session_id (same as instance_id)

2. palm_flows_session(session_id="...", flow_id="foo-bar", format="assistant")
   → read question, choices, mutation block

3. palm_flows_session_input(session_id="...", flow_id="foo-bar", input="plain text")
   → one answer per call; plain string only

4. Repeat 2 → 3 until status is "complete"
```

### Choice steps

When `choices` appear in the assistant response:

- Reply with the **slug**: `input="beta"`
- Or the **number** shown: `input="2"`

Do not send JSON like `{"answer": "beta"}`.

### Summary step (`include_summary: true`)

When `mutation.confirm_step` is true and the question asks to confirm:

- Send `input="yes"` **only if the user explicitly agreed**
- Never auto-confirm summary on inspect-only requests

### Strict token mode

If `PALM_MCP_REQUIRE_INPUT_TOKEN=1`, copy `mutation.input_token` from the last inspect into every `palm_flows_session_input` call.

---

## D. `palm_assist` aliases (alternative path)

| Goal | Call |
|------|------|
| Propose | `palm_assist(path=["design","propose"], params={body: {...}})` |
| Impact | `palm_assist(alias="design/impact", params={proposal_id: "prop-..."})` |
| Commit | `palm_assist(alias="design/commit", params={proposal_id: "prop-..."})` |
| Run session | `palm_assist(path=["flows","foo-bar","create"])` |

Full alias list: `palm://assist/routes` (domain `design`).

---

## E. Troubleshooting

| Symptom | What to do |
|---------|------------|
| `No handler registered for AnalyzeDefinitionImpactQuery` | **Restart** `palm-mcp` (server must reload after engine upgrade) |
| `valid: false` on propose | Read `blockers`; fix step slugs, choices, or validation |
| Commit rejected | Run `palm_design_impact` first; pass `commit_token` if strict mode |
| Flow not in list | `palm_flows_list()` — only **committed** flows appear |
| Session stuck | `palm_flows_session(..., format="assistant")` — never guess the step |

---

## F. Worked example: `foo-bar`

**Publish (revision 1):** propose body with two text steps → impact → commit.

**Improve (revision 2):** propose with `base_flow_id="foo-bar"`, add `include_summary`, choice step for `bar`, `min_length` on `foo` → impact → commit.

**Run:** `palm_flows_create_session(flow_id="foo-bar")` → input `my-foo` → input `beta` → input `yes` at summary → `status: complete`.