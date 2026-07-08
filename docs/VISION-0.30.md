# Vision 0.30 — Assist Design Entry

**Theme:** Make create/improve flow (and related Design Service work) discoverable from the Assist operator front door — without reimplementing Design inside Assist.

**Status:** **0.30.0**–**0.30.4** shipped · further UX gated  
**Depends on:** Assist 0.18–0.23 ✅ · Design Service 0.25+ ✅ · compositional design 0.27+ · document/KV 0.28–0.29  
**Design:** [assist-design-entry-design.md](superpowers/specs/2026-07-08-assist-design-entry-design.md)  
**Plan:** [assist-design-entry-0.30.md](superpowers/plans/2026-07-08-assist-design-entry-0.30.md)  
**ADR:** only if handoff gains a new `kind` (optional 0.30.3)

---

## Why 0.30

**Assist** answers “what should I do next with Palm?” **Design Service** answers “how do I safely publish definition changes?” Agents already use both — but **operator-entry** only triages a few demo business flows plus inspect-only catalog. Design remains a **separate MCP skill path** (`palm_design_*`), so agents who start at `palm_assist()` often never discover the propose → impact → commit loop and drift into free-form Python definitions instead.

| Symptom | Root cause |
|---------|------------|
| No “create flow from scratch” at operator-entry | Choices are `todo-builder` / `compositional-parent` / `inspect-only` only |
| Design tools unused after assist sessions | No in-session `actions` / hints pointing at `palm_design_*` |
| Operator feels “definitions + run demos” | Front door predates Design Service as a first-class domain |
| Enricher CTAs would not stick today | Assistant pipeline overwrites `actions` and strips intent from enricher input |

**0.30 does not invent a seventh service.** It **wires Assist discovery to Design**, with strict boundaries: Assist guides and hands off; Design owns catalog writes.

---

## Goal

| Shift | From | To |
|-------|------|-----|
| Operator-entry | Demo flows + inspect | **+ create/improve flow (and later resource) intents** |
| Design discovery | Skill/docs only | **Assistant `actions` + hints + optional design-entry scenario** |
| Agent path after “create flow” | Leave Assist / write Python | **Out-of-band `palm_design_*` from summary CTAs**, then run published flow |
| Complexity | Big-bang wizard | **Ladder:** docs → pipeline + discovery → scenario shell → handoff polish |

**Non-goals for the 0.30 track:**

- Reimplement Design Service inside Assist routes
- Replace `palm_design_*` tools
- Full visual flow builder or NL→AST codegen in Assist
- Absorb 0.23 deferred items (`palm-compose-guide`, process handoff, WebSocket) into the critical path
- Change bare `palm_assist()` default away from operator-entry (design is a **sibling** intent/scenario)

---

## Complexity ladder

| Phase | Theme | Behavior change? |
|-------|-------|------------------|
| **0.30.0** | Vision + design spec + plan + STATUS/AGENTS alignment | **No** |
| **0.30.1** | Action merge + intent visibility + operator-entry choices + inspect CTAs + intent-specific none-hints | **Yes** |
| **0.30.2** | `design-entry` assist scenario shell (step slug `intent`; still delegates writes) | **Yes** |
| **0.30.3** | Handoff polish; optional `kind: design` only if evidence demands | **Yes** |
| **0.30.4+** | Deeper UX (catalog pick, step collection) — gated | Optional |

**Engineering rules:** each phase independently testable; prefer pipeline-safe CTAs before wizards; wizards before new service methods; assert final assistant payload after `to_dict`, not enricher output alone; cleanup only when a phase is blocked.

**Delivery style:** ship when good enough — typically sequential commits on `master` per phase (or short-lived branches for tracking). Micro-release numbers mark **capability gates**, not a required GitHub PR stack.

---

## What 0.30.0 ships

- This vision
- Full design contracts (pipeline gaps, KD-1–KD-13, multi-turn script, PR/phase plan)
- STATUS priorities table for 0.30
- AGENTS pointer
- Future-tense skill/mcp stubs only where needed (present-tense agent docs wait for 0.30.1 behavior)

---

## Success criteria (track)

1. An agent starting with bare `palm_assist()` can choose create/improve flow without reading the Design skill first.
2. Final assistant views expose design tools as `actions` after design intent (post-pipeline merge).
3. Starting design-entry does **not** write the catalog; only Design commit does.
4. Assist still never imports Design write logic into route handlers for propose/commit.

---

## References

- [ADR-006 Assist domain](adr/006-assist-domain.md)
- [VISION-0.18 Assist](VISION-0.18-ASSIST.md)
- [VISION-0.25 Design Service](VISION-0.25.md)
- [design-flows skill](skills/palm/references/design-flows.md)
- Operator entry: `examples/definitions/operator_entry.py`
