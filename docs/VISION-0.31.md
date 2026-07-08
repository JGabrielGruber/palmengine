# Vision 0.31 — MCP Meta-Surface & Progressive Disclosure

**Theme:** Make Palm’s MCP operator surface **token-efficient for weak LLMs** by aligning the *host-visible tool catalog* with the meta-tool reality of `palm_assist` — progressive disclosure, measurable size, and an open ladder of improvements.

**Status:** **0.31.0 foundation documented** · implementation open-ended  
**Depends on:** Assist 0.18–0.30 ✅ · Design Service 0.25+ ✅ · MCP adapter 0.16+  
**Design:** [mcp-meta-surface-design.md](superpowers/specs/2026-07-08-mcp-meta-surface-design.md)  
**Plan:** [mcp-meta-surface-0.31.md](superpowers/plans/2026-07-08-mcp-meta-surface-0.31.md)

---

## Why 0.31

**0.30** made *operations* work through `palm_assist` (run flows, publish definitions, recover resources). Dogfood shows a low-context agent can create and drive a wizard with few calls.

The remaining cost is often **not** session JSON — it is **catalog bloat**:

| Symptom | Cause |
|---------|--------|
| Host injects **~40 tools** every request | MCP server registers full domain + pattern + app tools |
| Tool descriptions alone ~few k tokens | Rich weak-LLM docstrings (valuable, but always-on) |
| Agents still `search_tool` / web_search / open many resources | Discovery not progressive; docs can preload large |
| Feedback: “one meta-tool” pattern | Industry progressive disclosure; Palm has the meta-tool but not the slim catalog |

Measured baseline (in-process FastMCP, order-of-magnitude chars/4):

| Surface | ≈ tokens |
|---------|----------|
| Full tool catalog (39 tools) | ~5.3k |
| `palm_assist` alone | ~0.4k |
| Potential catalog savings if assist-only host surface | **~90%+** of tool inventory |
| `docs/mcp.txt` if fully loaded | ~3.9k (optional progressive load) |

**0.31 does not replace Assist or Design services.** It governs **how MCP exposes them** to agents and how we **measure** that exposure.

---

## Goal

| Shift | From | To |
|-------|------|-----|
| Host tool list | Always-full domain surface | **Configurable surfaces** (`assist` / `core` / `full` / experimental) |
| Agent default path | Many peer tools compete | **`palm_assist` is enough** for happy paths |
| Docs | Often all-or-nothing | **Progressive** (tiny always-on + on-demand resources) |
| Efficiency claims | Anecdote | **Measurable** catalog + turn size budgets |
| Roadmap | Closed feature list | **Open ladder** — ship valuable slices; leave room for host gateways, Code Mode, etc. |

**North-star operator loop (unchanged product meaning):**

```text
palm_assist()  →  run / design / inspect  →  next turn in one tool
```

---

## Principles

1. **Meta-tool at the edge, services in the middle** — thin MCP; real logic stays in `palm/services/*`.
2. **Progressive disclosure** — inject only what the model needs *now*.
3. **Power users keep full surface** — slim modes are default for agents, not a deletion of `palm_flows_*`.
4. **Measure before/after** — catalog inventory scripts and optional size logging.
5. **Open-ended evolution** — 0.31.x slices can ship independently; later work may include host-side gateways or true multi-meta-tool (discover + execute) without breaking assist.
6. **Core purity / SRP** — no Design logic in Assist; no pattern logic in `palm.common`.

---

## Non-goals (track-wide, not forever)

- Replacing REST or CLI surfaces
- Mandatory Code Mode / agent-written orchestrators (may appear as *optional* experiment)
- Removing per-domain tools from the codebase
- Guaranteeing exact tokenizer parity across models (use stable size proxies)

---

## Open ladder (illustrative, not a contract)

Phases are **capability gates**. Order can shift; new phases can be inserted.

| Phase | Theme | Intent |
|-------|--------|--------|
| **0.31.0** | Vision + design + plan + STATUS | Contracts only |
| **0.31.1** | Surface modes + catalog measurement | `PALM_MCP_SURFACE` (or equivalent); inventory harness |
| **0.31.2** | Assist-complete happy paths | Fold doctor/resume/list into assist routes/aliases so assist-only mode is usable |
| **0.31.3** | Progressive docs | Minimal always-on guide; deep docs on demand |
| **0.31.4** | Optional `palm_discover` (or routes-as-tool) | Query routes without huge `palm_assist` description |
| **0.31.5+** | Open | Host gateway docs, Code Mode experiment, pattern-tool virtualization, WebSocket stream (if still wanted), etc. |

---

## Success criteria (track)

1. A documented **assist-only** (or core) surface exists and runs dogfood: create flow + run session + doctor/resume without other MCP tools.
2. Catalog size for that surface is **materially smaller** than full (target: ≥70% reduction by size proxy).
3. Contributors know how to add capabilities **via assist routes/aliases**, not only new top-level tools.
4. Efficiency is **checkable** in CI or a `just` recipe (inventory report).

---

## Relationship to 0.30

| 0.30 | 0.31 |
|------|------|
| What agents can *do* via assist | How much *context* that costs |
| Design entry + lean turns | Meta-surface + progressive disclosure |
| Shipped through 0.30.8 | Starts at 0.31.0 docs |

---

## References

- Industry framing: progressive disclosure / meta-tool / Code Mode (external feedback)
- ADR-006 Assist · ADR-008 Design · MCP.md · mcp.txt · skills/palm
- Baseline measurement notes in design spec
