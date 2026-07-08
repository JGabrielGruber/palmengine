# Plan: Assist Design Entry (0.30)

**Vision:** [docs/VISION-0.30.md](../../VISION-0.30.md)  
**Design:** [2026-07-08-assist-design-entry-design.md](../specs/2026-07-08-assist-design-entry-design.md)  
**Status:** 0.30.0–0.30.4 ✅ · further optional  

Delivery: commit each phase when good enough (typically on `master`; short branches OK for tracking). Phases are capability gates, not a mandatory PR stack.

---

## Phase 0.30.0 — Docs foundation (this commit track)

**Goal:** Contracts only; no required runtime behavior change.

| Task | Done when |
|------|-----------|
| `docs/VISION-0.30.md` | Present, linked from STATUS |
| Design spec under `docs/superpowers/specs/` | Approved contracts (pipeline gaps, KD-9–13, multi-turn script) |
| This plan | Phase checklists below |
| `STATUS.md` Priorities | 0.30 table; 0.23 deferred kept separate |
| `AGENTS.md` | Pointer to VISION-0.30 |
| Skill / mcp.txt | Future-tense only if needed; no present-tense “operator-entry offers create-flow” until 0.30.1 |

**Acceptance:** Docs consistent; no new operator-entry choices in code.

---

## Phase 0.30.1 — Pipeline + discovery CTAs

**Goal:** Design discoverable from operator-entry and inspect; pipeline-correct final actions.

### Implementation order

1. **Intent visibility (KD-9)**  
   - Extend `OperatorViewContext` with `intent` / `answers_preview`.  
   - Populate in `AssistSessionContext.to_dict` from `detail` answers.

2. **Action merge (KD-10)**  
   - After `build_assistant_actions`, merge enricher/design CTAs; collection rules per design.  
   - Files: `schemas.py`, `views.py`, optionally small helper.

3. **inspect_catalog CTAs**  
   - Add create-flow design action to static payload in `AssistService.inspect_catalog` (bypasses session overwrite — high value, low risk).

4. **operator-entry**  
   - Choices: `create-flow`, `improve-flow` (+ keep existing).  
   - `handoff_map` design intents → `None`.  
   - `handoff_none_hints` metadata.  
   - Enricher/CTA helper branches on `intent`.

5. **handoff none-hint (small)**  
   - Intent-specific `operator_hint` when `kind: none` and design intent — still no `kind: design`.

6. **Tests** — assert **post-`to_dict`** assistant payload, not enricher alone:  
   - `tests/test_operator_entry_flow.py`  
   - `tests/test_assist_service.py`  
   - `tests/test_assistant_view.py` as needed  

7. **Docs** — mcp.txt / skill / design-flows present tense for shipped path.

### Acceptance (0.30.1)

1. create-flow session summary includes `palm_design_propose_flow` or `design/propose` in final `actions`.
2. `inspect_catalog` includes create CTA.
3. `handoff` after create-flow → `kind: none` + design-oriented hint (not generic “no handoff”).
4. No `kind: design`.

**Optional split:** 0.30.1a pipeline + inspect only; 0.30.1b wizard choices — only if review load requires it.

---

## Phase 0.30.2 — design-entry scenario shell

**Goal:** Guided assist scenario; zero catalog writes on start.

| Task | Notes |
|------|--------|
| `examples/definitions/design_entry.py` | Register `AssistContributor`; MCP aliases `design-entry/start` |
| Step slug **`intent`** | Modes create/improve/…; compatible with existing `handoff()` keying |
| Enricher | Design tool actions only; **no** `DesignService` import |
| Tests | Proposal repo count unchanged on start; propose not called |
| Optional | operator-entry action → `design-entry/start` |

**Acceptance:** Start scenario does not write catalog; final assistant payload has design actions.

---

## Phase 0.30.3 — Handoff polish (gated)

**Goal:** Post-terminal CTAs / `create_params`; optional `kind: design` only with evidence + MIGRATION.

- Do **not** re-litigate action merge (owned by 0.30.1).
- Gate full `kind: design` on product need (OQ-3).

---

## Phase 0.30.4+ — Optional deeper UX

Catalog pick, step collection wizard, compose-guide link — only if replay/agent evidence justifies.

---

## Normative multi-turn (0.30.1 primary path)

```text
1. palm_assist() → operator-entry
2. intent = create-flow | improve-flow
3. Land on summary (include_summary) with design actions + hint
4. Agent runs palm_design_propose_flow → impact → commit **out-of-band**
   (assist session may stay open; handoff NOT required)
5. Optional: handoff → kind none + same tool names in operator_hint
6. Run published flow via palm_flows_create_session (not assist handoff until later)
```

---

## Boundaries (do not violate)

| Domain | Owns |
|--------|------|
| Assist | Scenarios, views, handoff envelope, discovery CTAs |
| Design | propose / validate / impact / commit / discard |
| Definitions | Catalog CRUD / revisions plumbing |
| Flows execution | Business sessions after publish |

---

## Verification commands (per phase)

```bash
# After docs-only
just docs-check   # if available; else spot-check links

# After 0.30.1+
uv run pytest tests/test_operator_entry_flow.py tests/test_assist_service.py tests/test_assistant_view.py -q
# broader
just check   # or project equivalent
```

---

## References

Full contracts, KD table, risks, alternatives: design spec.
