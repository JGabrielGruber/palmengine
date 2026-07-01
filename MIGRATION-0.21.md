# Migration Guide — Palm 0.21

**Experimental policy:** 0.21 adds **human-native surfaces** (CLI, Explorer) and deepens the assistant envelope. Powertool defaults on `palm_flows_*` and flows REST are **unchanged** unless you opt in.

**Builds on:** [MIGRATION-0.20.md](MIGRATION-0.20.md) · **Design:** [docs/superpowers/specs/2026-07-01-assistant-expansion-design.md](docs/superpowers/specs/2026-07-01-assistant-expansion-design.md)

---

## 0.21 — Assistant expansion (human surfaces)

0.20 shipped the assistant envelope on assist REST/MCP. 0.21 makes it the **default human experience** in Palm's own CLI and Explorer, adds an `actions` block for agents, and offers opt-in assistant views on business flow sessions.

| Surface | Before (0.20) | After (0.21) |
|---------|---------------|--------------|
| **CLI REPL** | `flow start` + powertool `render_job_panel` | `assist start operator-entry` + `render_assistant_panel` |
| **Explorer** | Operator-entry via flows submit (powertool shape) | `/explorer/assist` catalog + HTMX workspace |
| **Assistant envelope** | `question`, `choices`, `hint`, `compose` | + `actions` block (progressive disclosure) |
| **Flows inspect** | Powertool only | Opt-in `format=assistant` on REST/MCP |

---

## Recommended entry (operators)

### CLI

**Before:**

```
flow start palm-operator-entry
```

**After (guided UX):**

```
assist start operator-entry
assist input todo-builder
assist handoff
```

Plain REPL lines route to `assist input` when an assist session is active. Flow commands remain available for direct business-session driving.

### Explorer

**Before:** `/explorer/flows/submit?flow_id=…` for operator-entry.

**After:** `/explorer/assist` → start scenario → interactive workspace (`#assist-workspace`) → handoff CTA to flows submit.

### MCP / REST (unchanged default)

Assist paths still default to assistant; flows/system stay powertool:

```
palm_assist(alias="operator-entry/start")
palm_assist(path=["flows","todo-builder","create"])   # powertool
```

---

## New: `actions` block (0.21.4)

Assistant turns may include an `actions` array — structured next steps derived from `next_commands`:

```json
{
  "question": "What would you like to do with Palm?",
  "choices": [{"n": 1, "label": "Todo Builder", "value": "todo-builder"}],
  "actions": [
    {"label": "Send answer", "path": ["assist", "session", "inst-1", "input"]},
    {"label": "Hand off to flow", "alias": "operator-entry/handoff", "params": {"session_id": "inst-1"}}
  ]
}
```

| Field | When present | Agent guidance |
|-------|--------------|----------------|
| `actions` | `format=assistant` only | Prefer over parsing `hint` for next-step discovery |
| `actions[].path` | Direct dispatch | Use with `palm_assist(path=…)` |
| `actions[].alias` | Registered shortcut | Use with `palm_assist(alias=…, params=…)` |

Powertool responses omit `actions`.

---

## New: Flows `format=assistant` opt-in (0.21.5)

Business flow sessions default to powertool. Humans who skip assist handoff can request the assistant envelope explicitly.

### MCP

```
palm_flows_session(session_id, format="assistant")
```

Default is `format="powertool"` (`compact` aliases to powertool).

### REST

```
GET /v1/api/flows/{flow_id}/session/{session_id}?format=assistant
POST …/input?format=assistant
```

Supported: `assistant` · `powertool` · `verbose` (default `powertool` on flows routes).

### Semantics

| Context | `scenario_id` | Enricher |
|---------|---------------|----------|
| Assist session | Set from metadata | Per-scenario enricher runs |
| Flow session (opt-in) | `None` | Generic humanize only |

`palm_assist` on `flows/*` paths stays powertool when only the tool-level `format=assistant` is set. Pass `params={"format": "assistant"}` on the flows session path to opt in via the proxy.

---

## Agent migration checklist

1. **Human operators** — point to `assist start operator-entry` (CLI) or `/explorer/assist` (browser).
2. **Parse `actions`** on assistant turns when building operator loops (optional; `hint` still valid).
3. **Keep `palm_flows_*` defaults** — no change required for automation agents.
4. **Opt-in flows assistant** — use `palm_flows_session(format="assistant")` or `?format=assistant` when human labels are needed on business sessions.
5. **Handoff unchanged** — `palm_assist(alias="operator-entry/handoff", params={"session_id": id})`.

---

## 0.21.7 — Weak-LLM MCP defaults

Hotfixes for coding agents that send sparse or null tool arguments (e.g. Llama, Composer fast models).

| Behavior | Detail |
|----------|--------|
| **Bare `palm_assist()`** | Starts `operator-entry` (assistant first turn); response includes `dispatch_default` hint |
| **Continue assist session** | `palm_assist(params={"session_id": "inst-…", "value": "yes"})` — path inferred to `assist/session/…/input` |
| **Null optional params** | `action: null` and `format: null` coerced to defaults (no MCP validation failure) |
| **MCP boot** | `shape_flow_session_view` lives in `palm/common/operator/` — REST no longer imports `palm.runtimes.mcp` |

**Examples:**

```
palm_assist()
palm_assist(params={"session_id": "inst-1", "value": "todo-builder"})
palm_assist(alias="operator-entry/handoff", params={"session_id": "inst-1"})
```

---

## 0.21.8 — Collection `add` + `value` one-shot

Weak LLMs often call `palm_wizard_collection_action(action=add, value="Title")` at menu phase. **0.21.8** chains menu → field automatically.

| Tool | One-shot call |
|------|---------------|
| `palm_wizard_collection_action` | `action="add", value="My todo title"` |
| `palm_flows_session_input` | `input="add", value="My todo title"` |

Powertool response shape unchanged. Menu-only `action=add` (no value) still opens the field phase for multi-field schemas.

---

## 0.21.9 — Assistant envelope on flows mutations

0.21.5 added `format=assistant` on session **inspect**. **0.21.9** extends opt-in shaping to **mutations** (input, collection actions).

| Surface | Opt-in call |
|---------|-------------|
| MCP `palm_flows_session_input` | `format="assistant"` |
| MCP `palm_wizard_collection_action` | `format="assistant"` |
| REST | `POST /v1/api/flows/{flow}/session/{id}/input?format=assistant` |
| `palm_assist` flows input | `params={"format": "assistant"}` on `…/input` path |

Collection menu assistant turns include an `actions` block (`Add item`, `Add titled item`) with `path` + `params` for `palm_assist` dispatch.

Powertool default unchanged when `format` is omitted.

**Next (0.21.10+):** unified `palm_assist` flows driving — see [weak-LLM plan](docs/superpowers/plans/2026-07-01-0.21.7-weak-llm-mcp.md).

---

## Release map (0.21.0–0.21.12)

| Version | Theme |
|---------|-------|
| 0.21.0 | Design spec |
| 0.21.1 | CLI `assist *` commands + `render_assistant_panel` |
| 0.21.2 | Explorer assist catalog + `assist_workspace` |
| 0.21.3 | Explorer HTMX verbs + handoff CTA |
| 0.21.4 | `actions` block + production enrichers + REST `catalog/flows` |
| 0.21.5 | Flows `format=assistant` opt-in (REST/MCP) |
| 0.21.6 | Migration + docs + verification |
| 0.21.7 | Weak-LLM MCP hotfixes (boot, null params, bare assist) |
| 0.21.8 | Collection `add` + `value` one-shot |
| 0.21.9 | Assistant envelope on flows mutations |
| 0.21.10+ | Unified assist, edit shortcuts, replay harness — planned |

---

## Extension (unchanged)

| Hook | Location |
|------|----------|
| `register_operator_view_builder` | `palm/common/operator/view_registry.py` |
| `register_assistant_enricher` | `palm/services/assist/registry.py` |
| `AssistContributor.assistant_enricher` | Auto-registers on `register_assist_contributor` |

No assist humanize logic in `palm/common/` — `just guard-common` enforced.

**0.22 deferred:** `palm-compose-guide` scenario, process handoff, WebSocket assist stream.