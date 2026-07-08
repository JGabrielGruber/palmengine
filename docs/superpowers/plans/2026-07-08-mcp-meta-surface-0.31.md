# Plan: MCP Meta-Surface (0.31) — open-ended

**Vision:** [docs/VISION-0.31.md](../../VISION-0.31.md)  
**Design:** [2026-07-08-mcp-meta-surface-design.md](../specs/2026-07-08-mcp-meta-surface-design.md)  
**Status:** 0.31.0–0.31.3 ✅ · 0.31.4+ open  

Delivery: commit when good enough; phases are capability gates, not a rigid stack. **New work can be inserted** if dogfood demands it.

---

## Phase 0.31.0 — Foundation (this commit)

| Task | Done when |
|------|-----------|
| VISION-0.31 | Present |
| Design spec | Surfaces, KD table, open questions |
| This plan | Ladder + how to extend |
| STATUS / AGENTS / CHANGELOG | Point at 0.31 |

**Acceptance:** no runtime behavior change required.

---

## Phase 0.31.1 — Surfaces + measurement (suggested next)

**Intent:** Make thin catalog real and checkable.

| Work item | Notes |
|-----------|--------|
| `PalmMcpConfig.surface` / `PALM_MCP_SURFACE` | `full` (default) · `assist` · maybe `core` |
| Wire `create_mcp_server` registration by surface | assist always; others gated |
| Inventory script | `scripts/mcp_catalog_inventory.py` or `just mcp-inventory` |
| Tests | tool count / names for `assist` vs `full` |
| Docs | MCP.md + mcp.txt + Grok config example |

**Acceptance:** `PALM_MCP_SURFACE=assist` → host sees primarily `palm_assist`; inventory reports sizes.

**Exit criteria for “good enough”:** dogfood create+run flow under assist-only (may need 0.31.2 first if gaps block).

---

## Phase 0.31.2 — Assist-complete happy paths

**Intent:** No mandatory peer tools for normal operator loops.

Gap matrix (fill during implementation):

| Capability | Assist path today? | Work |
|------------|-------------------|------|
| Run flow | yes | polish |
| Publish flow/resource | yes | polish |
| List flows | partial | ensure alias + assistant shape |
| Doctor | path exists | assistant envelope |
| Resume resource / child | domain tools | assist aliases |
| List waiting | domain | assist path optional |

**Acceptance:** written dogfood script: only `palm_assist` calls; no `palm_flows_*` / `palm_design_*` tool names required.

---

## Phase 0.31.3 — Progressive docs

**Intent:** Don’t pay full mcp.txt + skill on every session.

| Work item | Notes |
|-----------|--------|
| L0 description budget for palm_assist | Keep examples; link resource |
| L1 mini-guide resource | e.g. `palm://agent/card` |
| Host skill recipe | “load full guide only when stuck” |
| Optional: slim surface registers fewer resources | OQ-3 |

---

## Phase 0.31.4 — Optional discover meta-tool

**Intent:** Shrink always-on description further.

| Option | Description |
|--------|-------------|
| A | `palm_discover(query)` → top routes/aliases |
| B | Resource-only discovery (no new tool) |
| C | Skip — inventory + assist CTAs enough |

Choose after 0.31.1–0.31.2 dogfood.

---

## Phase 0.31.5+ — Open field

Candidates (not prioritized):

- `experimental` surface: Code Mode sketch  
- Host gateway documentation (external progressive disclosure)  
- CI token-budget tests on replay paths  
- Pattern tools never registered; only assist-invoked  
- Response size logging (`PALM_MCP_LOG_SIZES`)  
- Revisit default surface → `assist` with MIGRATION note  
- WebSocket assist stream (historical deferred)  
- Multi-agent / multi-tenant surface policies  

**Process for adding a phase:** one-line STATUS row + short design note if it changes contracts; no need for a new vision unless the theme shifts.

---

## How to check efficiency (operators)

```bash
# Catalog inventory (after 0.31.1)
just mcp-inventory
# or
uv run python scripts/mcp_catalog_inventory.py --surface full
uv run python scripts/mcp_catalog_inventory.py --surface assist

# Dogfood (manual)
PALM_MCP_SURFACE=assist uv run --extra mcp palm-mcp
# host: only palm_assist available → create foo-bar + run

# Per-turn size (ad hoc)
# len(json.dumps(assist_response)) / 4 ≈ tokens
```

Host UIs (Grok/Cursor) remain the source of truth for **end-to-end** billed tokens.

---

## Risks & rollback

| Risk | Rollback |
|------|----------|
| Assist-only breaks agents | Keep default `full`; document assist profile |
| Missing path | Add alias; don’t re-open full catalog by default |
| Over-planning | Prefer shipping 0.31.1 measurement early |

---

## References

Design KD-1–KD-7 · VISION-0.31 · MCP.md · 0.30 assist track
