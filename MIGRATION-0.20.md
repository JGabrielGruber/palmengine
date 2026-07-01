# Migration Guide — Palm 0.20

**Experimental policy:** 0.20 changes **response shapes** on assist surfaces. Per-domain MCP tools (`palm_flows_*`, …) keep powertool semantics.

**Builds on:** [MIGRATION-0.19.md](MIGRATION-0.19.md) · **Design:** [docs/superpowers/specs/2026-07-01-assistant-powertool-views-design.md](docs/superpowers/specs/2026-07-01-assistant-powertool-views-design.md)

---

## 0.20 — Assistant vs Powertool views

Palm now exposes two explicit operator read models:

| Mode | Audience | Default on | Key fields |
|------|----------|------------|------------|
| **Assistant** | Humans, conversational agents | `assist/*`, `palm_assist` (assist paths) | `question`, `choices`, `hint`, `compose`, `refs` |
| **Powertool** | Coding agents, automation | `palm_flows_*`, `palm_system_*`, flows/system via `palm_assist` | `instance_id`, `step`, `operator_hint`, `step_kind` |

**Assistant default is compose** — invoke context + wizard snapshot, humanized.

---

## Breaking-ish changes (assist surfaces)

### `palm_assist` on assist paths

**Before (0.19):** Powertool compact shape (`operator_hint`, `step_kind`, …).

**After (0.20):** Assistant envelope by default.

```json
{
  "session_id": "inst-…",
  "status": "waiting",
  "question": "What would you like to do with Palm?",
  "choices": [{"n": 1, "label": "Todo Builder", "value": "todo-builder"}],
  "hint": "Reply with a number or choice name.",
  "compose": {"step": "intent"}
}
```

**Opt-in to 0.19 shape:**

```
palm_assist(alias="operator-entry/start", format="powertool")
palm_assist(path=["assist","session",id], params={"format": "powertool"})
```

### `start_scenario` / operator-entry start

**Before:** ids-only (`session_id`, `job_id`, `status`).

**After:** First assistant turn (includes `question` + `choices`). No second inspect required.

### REST assist session

| Endpoint | Default response |
|----------|------------------|
| `GET /v1/api/assist/session/{id}` | Assistant envelope |
| `POST …/start` | Assistant first turn |
| `POST …/input` | Assistant envelope |

Query param: `?format=assistant|powertool|verbose` (default `assistant` on assist routes).

---

## Unchanged (powertool)

| Surface | Default |
|---------|---------|
| `palm_flows_session` | Powertool (`format=powertool`; `compact` alias; `format=assistant` opt-in since 0.21.5) |
| `palm_system_inspect_job` | Powertool |
| `palm_assist` on `flows/*`, `system/*` paths | Powertool (even when tool `format=assistant`) |

---

## Agent migration checklist

1. **Read `question` + `choices`** on assist responses instead of `operator_hint` + `step_kind`.
2. **Use `format=powertool`** on `palm_assist` if your agent still parses compact fields.
3. **Keep `palm_flows_*`** unchanged — no migration required for business session driving.
4. **Handoff** — still `palm_assist(alias="operator-entry/handoff", params={"session_id": id})`; response unchanged.

---

## Release map (0.20.0–0.20.5)

| Version | Theme |
|---------|-------|
| 0.20.0 | Design spec |
| 0.20.1 | `view_registry.py` in common |
| 0.20.2 | `assist/views.py` compose + humanize |
| 0.20.3 | Assist session defaults; start returns first turn |
| 0.20.4 | `palm_assist` `format=assistant` default |
| 0.20.5 | Migration + docs |

**0.21 shipped:** CLI assist commands, Explorer `/explorer/assist`, `actions` block, flows `format=assistant` opt-in — see [MIGRATION-0.21.md](MIGRATION-0.21.md).

---

## Extension (registry at edges)

| Hook | Location |
|------|----------|
| `register_operator_view_builder` | `palm/common/operator/view_registry.py` |
| `register_assistant_enricher` | `palm/services/assist/registry.py` |

No assist humanize logic in `palm/common/` — `just guard-common` enforced.