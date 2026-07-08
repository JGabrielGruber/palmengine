# Compositional Design Parity — 0.27 Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or executing-plans for phased delivery. Checkboxes track progress.

**Goal:** Extend Design Service and wizard declarative ergonomics so agents evolve **full compositional catalogs** with consistent schemas and dynamic human copy — validated by the `coconut-npc` reference flow.

**Architecture:** Business rules stay in `DesignService` / `DefinitionService` (ADR-008). Prompt binding per ADR-010. Pattern design contributors extended, not core engines modified.

**Vision:** [docs/VISION-0.27.md](../../VISION-0.27.md)  
**ADR:** [docs/adr/010-prompt-state-interpolation.md](../../adr/010-prompt-state-interpolation.md)

**Depends on:** 0.26.0 shipped (CQRS parity, design dispatch, MCP guides)

---

## Locked decisions

| # | Decision |
|---|----------|
| 1 | **Coconut is a reference example, not a product vertical** — regression + docs only |
| 2 | **Flat transform schema is canonical** — design validator aligns to builder; nested `transform` normalized optionally |
| 3 | **Resource design before process design** — `propose_resource` in 0.27.2; processes follow if impact model is clear |
| 4 | **Default resource failure = block** — truth-seeking; `skip`/`branch` opt-in per step |
| 5 | **`{{ state.key }}` only** — no Jinja loops/filters in 0.27.1 |
| 6 | **No DefinitionService write deprecation** — layered coexistence (ADR-008) |

---

## Phase 0.27.0 — Design schema parity

### Task 1: Fix wizard design contributor transform check

**Files:**
- Modify: `src/palm/patterns/wizard/bindings/design.py`
- Test: `tests/test_design_wizard_contributor.py` (create)

- [ ] Accept flat transform steps (`rule` + `source_key`) OR nested `transform` object
- [ ] Add test: `coconut-npc` options from `examples/definitions/coconut_npc.py` → `valid: true` via `validate_wizard_design_proposal`
- [ ] Add test: `transform-example` step list passes without nested wrapper

### Task 2: Optional normalizer in design prepare path

**Files:**
- Modify: `src/palm/services/design/` prepare/normalize (if central hook exists) or wizard builder entry

- [ ] If step has `transform` dict, merge into flat fields before `wizard_config_from_options`
- [ ] Document in `docs/skills/palm/references/design-flows.md`

### Task 3: Docs + example registration

**Files:**
- Create: `examples/definitions/coconut_npc.py` ✅
- Modify: `examples/README.md`, `CHANGELOG.md` [Unreleased]

- [ ] `palm doctor` lists `coconut-npc`
- [ ] Commit: `feat(0.27.0): design transform schema parity + coconut-npc example`

**Verification:**

```bash
uv run pytest tests/test_design_wizard_contributor.py tests/test_coconut_npc_flow.py -q
palm flow start coconut-npc   # manual smoke
```

---

## Phase 0.27.1 — Prompt state interpolation (ADR-010)

### Task 4: Shared binding helper

**Files:**
- Create: `src/palm/common/operator/prompt_binding.py` (or extend resource binding module)
- Modify: `src/palm/patterns/wizard/flow/phases/input.py`, `summary.py` (publish paths)

- [ ] `resolve_prompt_template(text, state) -> str`
- [ ] Unit tests: nested keys, missing keys, promotion from wizard answers

### Task 5: Wire coconut prompts (after interpolation ships)

**Files:**
- Modify: `examples/definitions/coconut_npc.py` — topic prompt includes `{{ state.mood_line }}`

- [ ] Replay test: after `friend` reputation, topic prompt contains sweet coconuts line

### Task 6: Docs

- [ ] Update VISION-0.27 success criteria
- [ ] ADR-010 status → Accepted
- [ ] `palm://agent/references/design-flows` — prompt binding section

**Verification:**

```bash
uv run pytest tests/test_prompt_binding.py tests/test_coconut_npc_flow.py -q
```

---

## Phase 0.27.2 — Design service: resources

### Task 7: DesignService `propose_resource`

**Files:**
- Modify: `src/palm/services/design/service.py`, `registry.py`
- Create: `src/palm/services/design/bindings/cqrs/` extensions
- Create: `src/palm/providers/*/bindings/design.py` stubs as needed

- [ ] Proposal envelope supports `kind: resource`
- [ ] Validate via provider/resource schema contributors
- [ ] Impact: list flows referencing `resource_ref`
- [ ] Commit publishes resource definition revision

### Task 8: MCP + REST

- [ ] `palm_design_propose_resource` or `palm_design_propose_definition(kind=...)`
- [ ] `palm://agent/references/design-flows` resource loop
- [ ] Parity test: in-process MCP propose → commit → `palm://definitions/resources`

---

## Phase 0.27.3 — Resource operator ergonomics

### Task 9: Doctor preflight

**Files:**
- Modify: `src/palm/services/system/` doctor checks

- [ ] Report REST `base_url` missing when REST resources registered
- [ ] Sample invoke `check-health` with clear pass/fail

### Task 10: Resource step resilience

**Files:**
- Modify: `src/palm/patterns/wizard/flow/phases/resource.py`

- [ ] Step param `on_resource_failure` with `block` | `skip` | `branch`
- [ ] Powertool inspect shows failure reason + remediation

---

## Phase 0.27.4 — Branching playbook

### Task 11: Agent skill reference

**Files:**
- Create: `docs/skills/palm/references/branching-flows.md`
- Modify: `src/palm/runtimes/mcp/resources.py`, `agent_assets.py`, `scripts/docs_check.py`

- [ ] MCP resource `palm://agent/references/branching-flows`
- [ ] Cross-link `coconut-npc` from `common-flows.md` and `design-flows.md`
- [ ] Sync bundled/Grok mirrors

---

## Release checklist (0.27.0 PyPI)

- [ ] `just docs-check` · `just guard-common` · `just check`
- [ ] CHANGELOG [0.27.0] section
- [ ] STATUS.md 0.27 shipped table
- [ ] Optional: MIGRATION-0.27.md if REST/design MCP surfaces change

---

## File map

| Path | 0.27 role |
|------|-----------|
| `examples/definitions/coconut_npc.py` | Reference branching wizard |
| `docs/VISION-0.27.md` | Release vision |
| `docs/adr/010-prompt-state-interpolation.md` | Prompt binding ADR |
| `src/palm/patterns/wizard/bindings/design.py` | Schema parity fix |
| `src/palm/services/design/` | Resource proposals (0.27.2) |
| `docs/skills/palm/references/branching-flows.md` | Weak-LLM playbook (0.27.4) |