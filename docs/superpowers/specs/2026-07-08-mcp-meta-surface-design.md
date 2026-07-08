# MCP Meta-Surface & Progressive Disclosure Design

| Field | Value |
|-------|--------|
| **Document** | Design specification + open-ended roadmap |
| **Date** | 2026-07-08 |
| **Status** | **Approved draft for 0.31 track** (open-ended) |
| **Target track** | **0.31 MCP meta-surface** |
| **Depends on** | Assist 0.30.x, MCP adapter, Design Service |
| **Vision** | [docs/VISION-0.31.md](../../VISION-0.31.md) |
| **Plan** | [docs/superpowers/plans/2026-07-08-mcp-meta-surface-0.31.md](../plans/2026-07-08-mcp-meta-surface-0.31.md) |

---

## Overview

Palm already has a **meta-dispatch tool** (`palm_assist`: path / alias / params → service domains). The industry “single meta-tool” efficiency pattern requires a second piece: **do not inject every domain tool into the model context by default**.

0.31 designs **MCP surfaces**, **measurement**, and an **open improvement ladder** so Palm can evolve toward assist-enough agents without painting a closed feature set.

---

## Background

### Current architecture

```
MCP Host (Grok / Cursor / …)
  injects ALL registered tools' name+description+schema
        ↓
palm-mcp (FastMCP)
  register_assist + flows + definitions + design + system
  + providers + resources + prompts + pattern/app contributors
        ↓
backend → palm.services (assist, design, execution, …)
```

`palm_assist` already implements **operational** progressive disclosure (one call shape, routes grow underneath). Host-level progressive disclosure is **not** enforced.

### Baseline (2026-07-08, in-process)

| Metric | Approx |
|--------|--------|
| Tool count | ~39 |
| Catalog size proxy (chars/4) | ~5.3k tokens |
| `palm_assist` alone | ~0.4k tokens |
| Catalog reduction if assist-only | ~90%+ of tool inventory |
| Per-turn assistant payloads (foo-bar) | Already lean after 0.30.x |

### Feedback alignment

External feedback recommends 1–4 meta-tools (discover, schema, execute, optional code). Palm maps as:

| Meta-tool role | Palm candidate |
|----------------|----------------|
| Execute / orchestrate | **`palm_assist`** (primary) |
| Discover | `palm://assist/routes`, skill resources; optional future `palm_discover` |
| Schema/docs | Tool descriptions + `palm://agent/*` resources |
| Code Mode | **Optional later experiment**, not required for 0.31 core |

---

## Goals & Non-Goals

### Goals

1. Define **MCP surface profiles** and how they register tools.
2. Make **assist-only** (or similarly thin) mode viable for end-to-end operator loops.
3. **Measure** catalog size (and optionally turn sizes).
4. Keep full surface for integrators and power users.
5. Leave the track **open-ended** for further progressive-disclosure ideas.

### Non-Goals

- Deleting `palm_flows_*` / `palm_design_*` from the tree
- Forcing all hosts to use slim mode
- Exact multi-model tokenizer accuracy
- Closed exhaustive 0.31 feature freeze

---

## Proposed Design

### Surface profiles

| Profile id | Tools (intent) | Audience |
|------------|----------------|----------|
| **`full`** | Current behavior (all domain + pattern/app tools) | Default for backward compatibility / power users |
| **`assist`** | Essentially **`palm_assist` only** (+ maybe health) | Weak-LLM agents; token-sensitive hosts |
| **`core`** | assist + small escape hatch set (TBD: doctor, list waiting?) | Middle ground |
| **`experimental`** | Open — Code Mode, discover tool, etc. | Research |

**Configuration (illustrative):**

```text
PALM_MCP_SURFACE=full|assist|core|experimental
```

or config field on `PalmMcpConfig`. Default remains **`full`** until dogfood proves assist-only default is safe.

### Registration model

```python
# conceptual
def create_mcp_server(...):
    surface = resolve_surface(config)  # full | assist | core | ...
    register_assist_tools(mcp, backend)  # always
    if surface.includes("flows"):
        register_flow_tools(...)
    ...
    if surface.includes("patterns"):
        register_pattern_mcp_tools(...)
```

**Always-on:** `palm_assist` (+ core resources optional).  
**Never in assist-only:** pattern sprawl tools unless exposed via assist path.

### Assist-complete coverage (for thin surface)

Happy paths that must work with **only** `palm_assist` (aliases/paths):

| Need | Approach |
|------|----------|
| Start / drive flows | Already (0.30.6) |
| Publish flow/resource | Already (0.30.4–0.30.5) |
| List flows | `assist/catalog/flows` or new alias |
| Doctor / resource preflight | `assist/doctor` (exists) — ensure assistant-shaped |
| Resume resource / child wait | aliases under assist or flows path via assist |
| Cancel / list waiting | system paths via assist dispatch if not already |

Gap analysis is **implementation work** (0.31.2+), not frozen here.

### Progressive documentation

| Layer | Content | When loaded |
|-------|---------|-------------|
| L0 | Short `palm_assist` description (examples only) | Always (tool catalog) |
| L1 | Tiny operator card resource (~few hundred tokens) | Optional first read |
| L2 | Full mcp.txt / skill / design-flows | On demand |

Open question: whether slim surface should **omit** large default resources or serve a **stub** guide.

### Measurement

| Artifact | Purpose |
|----------|---------|
| `scripts/mcp_catalog_inventory.py` (or `just mcp-inventory`) | List tools, chars, est tokens, per surface |
| Optional `PALM_MCP_LOG_SIZES=1` | Log response sizes for assist_dispatch |
| CI optional | Assert assist surface tool count ≤ N |

Proxy: `tokens ≈ len(utf8) / 4` for relative comparisons.

### Optional later: true multi-meta-tool

```
palm_discover(query) → short route/tool hits
palm_assist(...)     → execute
```

Or host-side MCP gateway outside Palm. Track remains open.

---

## Key Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| **KD-1** | 0.31.0 is **docs/contracts** first | Same discipline as 0.30.0 |
| **KD-2** | Default surface stays **`full`** until assist-only is proven | No silent break for existing hosts |
| **KD-3** | **`palm_assist` is the primary meta-execute tool** | Already shipped; don’t invent a parallel execute API |
| **KD-4** | Thin modes are **registration filters**, not service removals | SRP; power users keep full |
| **KD-5** | Measure with **size proxies** + dogfood | Practical |
| **KD-6** | Roadmap is a **ladder**, not a closed sprint list | User request: open-ended |
| **KD-7** | Code Mode / host gateways are **optional extensions** | Avoid complexity tax early |

---

## Alternatives Considered

| Alternative | Trade-off |
|-------------|-----------|
| Always only palm_assist | Breaks existing multi-tool agent configs |
| Host-only filtering (no Palm change) | Works but not portable across Grok/Cursor setups |
| Code Mode first | High complexity; Palm tool count is still modest (~40) |
| Shrink all tool descriptions | Helps full surface; doesn’t beat 90% catalog cut |

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Assist-only missing a path agents need | High | Gap matrix + dogfood before default change |
| Hosts ignore surface env | Medium | Document Grok/Cursor config recipes |
| Description still long on palm_assist | Low | Progressive docs; optional discover tool |
| Contributors keep adding top-level tools | Medium | AGENTS.md: prefer assist routes in slim era |

---

## Open Questions (intentionally open)

| # | Question | Notes |
|---|----------|-------|
| OQ-1 | When (if ever) is default surface `assist`? | After dogfood + migration note |
| OQ-2 | Is `core` needed or only `assist` + `full`? | Product taste |
| OQ-3 | Include MCP resources in slim mode? | Catalogs vs pure assist |
| OQ-4 | Ship `palm_discover` vs rely on resources? | Token vs UX |
| OQ-5 | Code Mode experiment under `experimental`? | Optional |
| OQ-6 | Integrate host gateways (external)? | Document, don’t own |

---

## References

- [VISION-0.31.md](../../VISION-0.31.md)
- [VISION-0.30.md](../../VISION-0.30.md) · [ADR-006](../../adr/006-assist-domain.md)
- [docs/MCP.md](../../MCP.md) · [docs/mcp.txt](../../mcp.txt)
- Baseline inventory: in-process `list_tools()` size analysis (2026-07-08)
- Industry: progressive disclosure / meta-tool / Code Mode (external feedback)

---

## Appendix — Open development themes

These may become 0.31.x or later tracks without a new vision:

- Assist description budget (max chars) + tests  
- Virtualize pattern tools behind assist only  
- Per-domain “schema on demand” resource `palm://assist/tools/{name}`  
- Replay harness: token budget on create+run foo-bar  
- WebSocket assist stream (deferred from 0.23) if still desired  
- Multi-tenant surface policy for remote palm-mcp  

*End of design document.*
